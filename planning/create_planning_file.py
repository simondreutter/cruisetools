import os

from qgis.core import (
    QgsField,
    QgsFields,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterCrs,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSink,
    QgsCoordinateReferenceSystem,
    QgsProcessingException,
    QgsProcessingUtils,
    QgsWkbTypes
)

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from PyQt5.QtGui import QIcon

from .planning import Planning
from .. import utils

class CreatePlanningFile(QgsProcessingAlgorithm, Planning):
    """Create Planning File."""

    # Processing parameters
    # inputs:
    FILE_TYPE = 'FILE_TYPE'
    CRS = 'CRS'
    MBES = 'MBES'
    # outputs:
    OUTPUT = 'OUTPUT'

    def __init__(self):
        """Initialize CreatePlanningFile."""
        super(CreatePlanningFile, self).__init__()
        
        # style files for planning layer
        self.style_planning_lines = ':/plugins/cruisetools/styles/style_planning_lines.qml'
        self.style_planning_points = ':/plugins/cruisetools/styles/style_planning_points.qml'
        
        # initialize default configuration
        self.initConfig()

    def initConfig(self):
        """Get default values from CruiseToolsConfig."""
        self.file_type = self.config.getint(self.module, 'file_type')
        self.default_crs = self.config.get(self.module, 'default_crs')
        self.crs = QgsCoordinateReferenceSystem()
        self.crs.createFromString(self.default_crs)
        self.mbes = self.config.getboolean(self.module, 'mbes')

    def initAlgorithm(self, config=None):  # noqa
        self.file_types = [self.tr('Point Planning'),
                           self.tr('Line Planning')]
        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.FILE_TYPE,
                description=self.tr('Planning File Type'),
                options=self.file_types,
                defaultValue=self.file_type,
                optional=False,
                allowMultiple=False)
        )
        self.addParameter(
            QgsProcessingParameterCrs(
                name=self.CRS,
                description=self.tr('Output CRS'),
                optional=True,
                defaultValue=self.crs)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.MBES,
                description=self.tr('MBES Planning Layer'),
                optional=False,
                defaultValue=self.mbes)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.OUTPUT,
                description=self.tr('Planning File'),
                type=QgsProcessing.TypeVectorLine,
                defaultValue=None,
                optional=False,
                createByDefault=True)
        )

    def processAlgorithm(self, parameters, context, feedback):  # noqa
        # get input variables as self.* for use in post processing
        file_type = self.parameterAsEnum(parameters, self.FILE_TYPE, context)
        crs = self.parameterAsCrs(parameters, self.CRS, context)
        mbes = self.parameterAsBoolean(parameters, self.MBES, context)
        
        # if CRS is None, use project CRS
        if not crs.isValid():
            crs = context.project().crs()
        
        # set new default values in config
        feedback.pushConsoleInfo(self.tr('Storing new default settings in config...'))
        self.config.set(self.module, 'file_type', file_type)
        self.config.set(self.module, 'default_crs', crs.authid())
        self.config.set(self.module, 'mbes', mbes)
        
        # fields to be created
        fields = QgsFields()
        
        # check for type (point or line) and set creat parameters
        feedback.pushConsoleInfo(self.tr('Creating output fields...'))
        if file_type == 0:
            geom_type = QgsWkbTypes.Point
            fields.append(QgsField('name', QVariant.String, '', 0, 0))
            fields.append(QgsField('notes', QVariant.String, '', 0, 0))
        elif file_type == 1:
            geom_type = QgsWkbTypes.LineString
            fields.append(QgsField('name', QVariant.String, '', 0, 0))
            fields.append(QgsField('turn_radius_nm', QVariant.Double, '', 4, 2))
            fields.append(QgsField('speed_kn', QVariant.Double, '', 4, 2))
            fields.append(QgsField('time_h', QVariant.Double, '', 4, 2))
            if mbes:
                fields.append(QgsField('mbes_swath_angle', QVariant.Int, '', 3, 0))
                fields.append(QgsField('mbes_swath_angle_port', QVariant.Int, '', 3, 0))
                fields.append(QgsField('mbes_swath_angle_stb', QVariant.Int, '', 3, 0))
            fields.append(QgsField('notes', QVariant.String, '', 0, 0))
        
        # creating feature sink
        feedback.pushConsoleInfo(self.tr('Creating feature sink...'))
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, fields, geom_type, crs)
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
        
        # make variables accessible for post processing
        self.file_type = file_type
        self.output = dest_id
        
        result = {self.OUTPUT : self.output}
        
        return result

    def postProcessAlgorithm(self, context, feedback):  # noqa
        # get layer from source and context
        planning_layer = QgsProcessingUtils.mapLayerFromString(self.output, context)
        
        if self.file_type == 0:
            style = self.style_planning_points
            style_name = 'Cruise Tools Point Planning'
            style_desc = 'Point Planning style for QGIS Symbology from Cruise Tools plugin'
        elif self.file_type == 1:
            style = self.style_planning_lines
            style_name = 'Cruise Tools Line Planning'
            style_desc = 'Line Planning style for QGIS Symbology from Cruise Tools plugin'
        
        # loading Cruise Tools Planning style from QML style file
        feedback.pushConsoleInfo(self.tr('Loading style...'))
        planning_layer.loadNamedStyle(style)
        
        # writing style to GPKG (or else)
        feedback.pushConsoleInfo(self.tr('Writing style to output...\n'))
        planning_layer.saveStyleToDatabase(name=style_name, description=style_desc, useAsDefault=True, uiFileContent=None)
        
        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Planning file created!\n'))
        
        result = {self.OUTPUT : self.output}
        
        return result

    def name(self):  # noqa
        return 'createplanningfile'

    def icon(self):  # noqa
        icon = QIcon(f'{self.plugin_dir}/icons/create_planning_file.png')
        return icon
    
    def displayName(self):  # noqa
        return self.tr('Create Planning File')

    def group(self):  # noqa
        return self.tr('Planning')

    def groupId(self):  # noqa
        return 'planning'

    def tr(self, string):  # noqa
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):  # noqa
        doc = f'{self.plugin_dir}/doc/create_planning_file.help'
        if not os.path.exists(doc):
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):  # noqa
        return CreatePlanningFile()
