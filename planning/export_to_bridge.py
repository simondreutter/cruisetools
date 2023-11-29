# -*- coding: utf-8 -*-
import os
import csv

from qgis.core import (
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsField,
    QgsFields,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFileDestination,
    QgsWkbTypes)

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from PyQt5.QtGui import QIcon

from .planning import Planning
from .. import utils

class ExportToBridge(QgsProcessingAlgorithm, Planning):
    """Export To Bridge"""

    #processing parameters
    # inputs:
    INPUT = 'INPUT'
    # outputs:
    EXPORT_FORMAT = 'EXPORT_FORMAT'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        """Initialize ExportToBridge"""
        super(ExportToBridge, self).__init__()
        
        # initialize default configuration
        self.initConfig()

    def initConfig(self):
        """Get default values from CruiseToolsConfig"""
        self.export_format = self.config.getint(self.module, 'export_format')

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.INPUT,
                description=self.tr('Input planning layer'),
                types=[QgsProcessing.TypeVectorPoint,QgsProcessing.TypeVectorLine],
                defaultValue=None,
                optional=False)
        )
        self.export_types = [self.tr('CSV [all fields]'),
                             self.tr('CSV [SAM Route Exchange style]')]
        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.EXPORT_FORMAT,
                description=self.tr('Export format'),
                options=self.export_types,
                defaultValue=self.export_format,
                optional=False,
                allowMultiple=False)
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                name=self.OUTPUT,
                description=self.tr('Bridge export'),
                fileFilter='CSV (*.csv)',
                defaultValue=None,
                optional=False,
                createByDefault=False)
        )  

    def processAlgorithm(self, parameters, context, feedback):
        # get input variables
        source = self.parameterAsSource(parameters, self.INPUT, context)
        export_format = self.parameterAsEnum(parameters, self.EXPORT_FORMAT, context)
        output = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        
        # set new default values in config
        feedback.pushConsoleInfo(self.tr(f'Storing new default settings in config...'))
        self.config.set(self.module, 'export_format', export_format)
        
        # coordinate transformation
        trans = QgsCoordinateTransform(source.sourceCrs(), QgsCoordinateReferenceSystem('EPSG:4326'), context.transformContext())
        
        # geometry type
        geom_type = QgsWkbTypes.geometryType(source.wkbType())
        
        if geom_type == QgsWkbTypes.LineGeometry:
            # fields to be created (empty)
            feedback.pushConsoleInfo(self.tr(f'Creating attribute fields...'))
            fields = QgsFields()
            
            # fields from feature source
            source_fields = source.fields()
            
            # if source does not have fid field, create it in fields
            if 'fid' not in source_fields.names():
                fields.append(QgsField('fid', QVariant.Int, '', 4, 0))
            
            # add all fields from source to fields variable
            for field in source_fields:
                fields.append(field)
            
            # get features from source
            features = source.getFeatures()
            
            # get vertices from features
            feedback.pushConsoleInfo(self.tr(f'Converting lines to vertices...'))
            points = self.lines_to_vertices(features, fields)
        
        elif geom_type == QgsWkbTypes.PointGeometry:
            # get points directly
            points = source.getFeatures()
        
        else:
            feedback.reportError(self.tr('Unknown Geometry WKB Type'), fatalError=True)
            return {}
        
        # empty table for point features and their attributes
        table = []
        
        # create dict holding all features with fieldnames and geometry
        feedback.pushConsoleInfo(self.tr(f'Extracting feature attributes...'))
        for i, feature in enumerate(points):
            feature_fields = feature.fields().names()
            feature_attributes = feature.attributes()
            
            # add minimum of required fields if they don't exist
            if not 'fid' in feature_fields:
                feature_fields.append('fid')
                feature_attributes.append(i+1)
            if not 'name' in feature_fields:
                feature_fields.append('name')
                feature_attributes.append('')
            
            # zip lists to dict
            feature_dict = dict(zip(feature_fields, feature_attributes))
            
            # get geometry of feature
            geom = feature.geometry().asPoint()
            
            # transform geometry to EPSG:4326 CRS
            feedback.pushConsoleInfo(self.tr(f'Adding coordinates...'))
            geom4326 = trans.transform(geom)
            feature_dict['lat_DD'] = geom4326.y()
            feature_dict['lon_DD'] = geom4326.x()
            
            # convert DD to DDM
            lat_ddm, lon_ddm = utils.dd2ddm(geom4326.y(), geom4326.x())
            feature_dict['lat_DDM'] = lat_ddm
            feature_dict['lon_DDM'] = lon_ddm
            
            # clean up NULL values:
            for key, value in feature_dict.items():
                if not type(value) in [float, int, str, bool]:
                    if value.isNull():
                        feature_dict[key] = None
            
            table.append(feature_dict)
        
        # export functions
        feedback.pushConsoleInfo(self.tr(f'Exporting table...'))
        if export_format == 0:
            error, result = self.export_csv(table, output)
        elif export_format == 1:
            error, result = self.export_SAM_route(table, output)
        
        if error:
            feedback.reportError(self.tr(result), fatalError=True)
            return {}
        
        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Export file created!\n'))
        
        result = {self.OUTPUT : output}
        
        return result

    def export_csv(self, table, output):
        """Export table as Comma Separated Value [CSV]

        Parameters
        ----------
        table : list
            list of feature attribute dictionaries
        output : str
            output CSV file

        Returns
        -------
        error : boolean
            0/1 - no error/error
        result : str
            output or error msg if error == 1

        """
        # open file with ANSI encoding for excel to understand things
        with open(output, 'w', newline='', encoding='ansi') as csvfile:
            # create csv writer with excel dialect
            csv_writer = csv.writer(csvfile, dialect='excel')
            
            # write header as list of fields
            header = [x for x in table[0].keys()]
            csv_writer.writerow(header)
            
            # loop over features
            for feature in table:
                # write feature attributes
                row = [str(feature[key]).replace('NULL', '').replace('None', '') for key in feature.keys()]
                csv_writer.writerow(row)
        
        return 0, output

    def export_SAM_route(self, table, output):
        """Export table as SAM Route to bridge Comma Separated Value [CSV]

        Parameters
        ----------
        table :
            list of feature attribute dictionaries
        output :
            output CSV file

        Returns
        -------
        error : boolean
            0/1 - no error/error
        result : str
            output or error msg if error == 1

        """
        # open file with ANSI encoding for excel to understand things
        with open(output, 'w', newline='', encoding='ansi') as csvfile:
            # create csv writer with excel dialect
            csv_writer = csv.writer(csvfile, dialect='excel')
            
            # write header as list of fields
            header = ['Name', 'Latitude [°]', 'Longitude [°]', 'Turn Radius [NM]', 'Max. Speed [kn]', 'XTD [m]', 'Sailmode', 'Additional Notes']
            csv_writer.writerow(header)
            
            # loop over features
            for feature in table:
                # concat name and fid for 'Name' column
                if feature['name'] == ('' or None):
                    name_out = feature['fid']
                else:
                    name_out = str(feature['fid']) + '_' + str(feature['name'])
                
                # add additional fields as None,  if they don't exist
                for key in ['turn_radius_nm', 'speed_kn', 'notes']:
                    if not key in feature:
                        feature[key] = None
                
                # compose row
                row = [name_out,
                      round(feature['lat_DD'], 6),
                      round(feature['lon_DD'], 6),
                      feature['turn_radius_nm'],
                      feature['speed_kn'],
                      '',
                      '',
                      feature['notes']]
                
                # write feature attributes
                csv_writer.writerow(row)
        
        return 0, output

    def name(self):
        return 'exporttobridge'

    def icon(self):
        icon = QIcon(f'{self.plugin_dir}/icons/export_to_bridge.png')
        return icon
    
    def displayName(self):
        return self.tr('Export To Bridge')

    def group(self):
        return self.tr('Planning')

    def groupId(self):
        return 'planning'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        doc = f'{self.plugin_dir}/doc/export_to_bridge.help'
        if not os.path.exists(doc):
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return ExportToBridge()
