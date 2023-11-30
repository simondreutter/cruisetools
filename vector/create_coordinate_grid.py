import os

from qgis.core import (
    QgsCoordinateTransform,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsPointXY,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterExtent,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterNumber,
    QgsCoordinateReferenceSystem,
    QgsProcessingParameterVectorDestination,
    QgsProcessingUtils,
    QgsWkbTypes
)

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from PyQt5.QtGui import QIcon

from .vector import Vector
from .. import utils

def opt_label(label, interval):
    """Optimize label.

    Parameters
    ----------
    label : str
        Label string from utils.dd2ddm()
    interval : float
        Coordinate grid interval

    Returns
    -------
    label : str
        Optimized label string
    
    """
    # check whether minutes and decimal minutes need to be shown
    if interval % 1 == 0:
        minutes = False
        dec_minutes = False
    else:
        minutes = True
        if (interval * 60) % 1 == 0:
            dec_minutes = False
        else:
            dec_minutes = True
    
    # optimize label
    # label from utils.dd2ddm(): 180°00.000'W
    if label == "180°00.000'W":
        label = ''
        return label
    if label == "180°00.000'E":
        label = label.replace('E', '') 
    
    if minutes == False:
        label = label.replace("00.000'", '')
    
    if dec_minutes == False:
        label = label.replace('.000', '')
    
    # kill leading zeros
    if label.startswith('0'):
        label = label[1:]
    if label.startswith('0'):
        label = label[1:]
    # save the 0° label
    if label.startswith('°'):
        label = f'0{label}'
    
    return label

class CreateCoordinateGrid(QgsProcessingAlgorithm, Vector):
    """Coordinate Grid Generator."""

    # Processing parameters
    # inputs:
    EXTENT = 'EXTENT'
    INTERVAL_LON = 'INTERVAL_LON'
    INTERVAL_LAT = 'INTERVAL_LAT'
    POLE_GAP = 'POLE_GAP'
    DENSITY_FACTOR = 'DENSITY_FACTOR'
    # outputs:
    OUTPUT = 'OUTPUT'

    def __init__(self):
        """Initialize CreateCoordinateGrid."""
        super(CreateCoordinateGrid, self).__init__()
        
        # style files for planning layer
        self.style_coordinate_grid = ':/plugins/cruisetools/styles/style_coordinate_grid.qml'
        
        # initialize default configuration
        self.initConfig()

    def initConfig(self):
        """Get default values from CruiseToolsConfig."""
        self.interval_lon = self.config.getfloat(self.module, 'interval_lon')
        self.interval_lat = self.config.getfloat(self.module, 'interval_lat')
        self.pole_gap = self.config.getfloat(self.module, 'pole_gap')
        self.densify_factor = self.config.getint(self.module, 'densify_factor')

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterExtent(
                name=self.EXTENT,
                description=self.tr('Grid extent'),
                defaultValue='-180.0,180.0,-90.0,90.0 [EPSG:4326]')
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.INTERVAL_LON,
                description=self.tr('Longitude interval [degrees]'),
                type=QgsProcessingParameterNumber.Double,
                optional=False,
                defaultValue=self.interval_lon,
                minValue=0.,
                maxValue=360.)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.INTERVAL_LAT,
                description=self.tr('Latitude interval [degrees]'),
                type=QgsProcessingParameterNumber.Double,
                optional=False,
                defaultValue=self.interval_lat,
                minValue=0.,
                maxValue=180.)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.POLE_GAP,
                description=self.tr('Pole gap [degree]'),
                type=QgsProcessingParameterNumber.Double,
                optional=False,
                defaultValue=self.pole_gap,
                minValue=0.,
                maxValue=90.)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.DENSITY_FACTOR,
                description=self.tr('Density factor'),
                type=QgsProcessingParameterNumber.Integer,
                optional=False,
                defaultValue=self.densify_factor,
                minValue=0,
                maxValue=100)
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                name=self.OUTPUT,
                description=self.tr('Coordinate grid'),
                defaultValue=None,
                optional=False,
                createByDefault=False)
        )

    def processAlgorithm(self, parameters, context, feedback):  # noqa
        # CRS geo
        crs = QgsCoordinateReferenceSystem('EPSG:4326')
        
        # get input variables
        extent = self.parameterAsExtent(parameters, self.EXTENT, context, crs)
        self.interval_lon = self.parameterAsDouble(parameters, self.INTERVAL_LON, context)
        self.interval_lat = self.parameterAsDouble(parameters, self.INTERVAL_LAT, context)
        self.pole_gap = self.parameterAsDouble(parameters, self.POLE_GAP, context)
        self.densify_factor = self.parameterAsDouble(parameters, self.DENSITY_FACTOR, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        
        # set new default values in config
        feedback.pushConsoleInfo(self.tr('Storing new default settings in config...'))
        self.config.set(self.module, 'interval_lon', self.interval_lon)
        self.config.set(self.module, 'interval_lat', self.interval_lat)
        self.config.set(self.module, 'pole_gap', self.pole_gap)
        self.config.set(self.module, 'densify_factor', self.densify_factor)
        
        # list for line features
        features = []
        
        # fields to be created
        fields = QgsFields()
        
        # set create parameters
        geom_type = QgsWkbTypes.LineString
        fields.append(QgsField('latlon', QVariant.String, '', 0, 0))
        fields.append(QgsField('deg', QVariant.Double, '', 10, 6))
        fields.append(QgsField('label', QVariant.String, '', 0, 0))
        
        # creating feature sink
        feedback.pushConsoleInfo(self.tr('Creating feature sink...'))
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, fields, geom_type, crs)
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
        
        # create grid
        feedback.pushConsoleInfo(self.tr('Creating grid...'))
        
        # some parameters
        xmin = max((-180., extent.xMinimum()))
        xmax = min((180., extent.xMaximum()))
        ymin = max((-90 + self.pole_gap, extent.yMinimum()))
        ymax = min((90 - self.pole_gap, extent.yMaximum()))
        stepsize_lon = self.interval_lon / self.densify_factor
        stepsize_lat = self.interval_lat / self.densify_factor
        
        # prepare steps once with interval and once with dense interval
        
        # x / lon
        # steps from 0 to +180 and from 0 to -180 with interval_lon
        a = np.arange(0, xmax + stepsize_lon, self.interval_lon)
        b = np.arange(0, xmin - stepsize_lon, -self.interval_lon)
        # concat both directions
        lon_steps = np.concatenate((a, b), axis=None)
        # clip to min max and delete 0 duplicates
        lon_steps = np.unique(np.clip(lon_steps, xmin, xmax))
        # steps from 0 to +180 and from 0 to -180 with stepsize_lon (dense)
        a = np.arange(0, xmax + stepsize_lon, stepsize_lon)
        b = np.arange(0, xmin - stepsize_lon, -stepsize_lon)
        # concat both directions
        lon_steps_dense = np.concatenate((a, b),axis=None)
        # clip to min max and delete 0 duplicates
        lon_steps_dense = np.clip(lon_steps_dense, xmin, xmax)
        # add xmin and xmax if not already in lon_steps
        if xmin not in lon_steps:
            lon_steps = np.append(lon_steps, xmin)
        if xmax not in lon_steps:
            lon_steps = np.append(lon_steps, xmax)
        # sort by value
        lon_steps.sort()
        lon_steps_dense.sort()
        
        # y / lat
        # steps from 0 to ymax and from 0 to ymin with interval_lat
        a = np.arange(0, ymax + stepsize_lat, self.interval_lat)
        b = np.arange(0, ymin - stepsize_lat, -self.interval_lat)
        # concat both directions
        lat_steps = np.concatenate((a, b), axis=None)
        # clip to min max and delete 0 duplicates
        lat_steps = np.unique(np.clip(lat_steps, ymin, ymax))
        # steps from 0 to ymax and from 0 to ymin with stepsize_lat (dense)
        a = np.arange(0, ymax + stepsize_lat, stepsize_lat)
        b = np.arange(0, ymin - stepsize_lat, -stepsize_lat)
        # concat both directions
        lat_steps_dense = np.concatenate((a, b),axis=None)
        # clip to min max and delete 0 duplicates
        lat_steps_dense = np.unique(np.clip(lat_steps_dense, ymin, ymax))
        # add ymin and ymax if not already in lat_steps
        if ymin not in lat_steps:
            lat_steps = np.append(lat_steps, ymin)
        if ymax not in lat_steps:
            lat_steps = np.append(lat_steps, ymax)
        # sort by value
        lat_steps.sort()
        lat_steps_dense.sort()
        
        # create features
        # x / lon
        for lon in lon_steps:
                # create geom and attributes
                vertices = []
                for lat in lat_steps_dense:
                    vertices.append(QgsPointXY(lon,lat))
                latlon = 'lon'
                deg = float(lon)
                _, lon_DDM = utils.dd2ddm(0, lon)
                label = opt_label(lon_DDM, self.interval_lon)
                geom = QgsGeometry.fromPolylineXY(vertices)
                
                # initialize line feature
                feature = QgsFeature(fields)
                
                # set geometry
                feature.setGeometry(geom)
                
                # set attributes
                feature.setAttribute('latlon', latlon)
                feature.setAttribute('deg', deg)
                feature.setAttribute('label', label)
                
                # append feature to features list
                if feature.hasGeometry() and feature.isValid():
                    features.append(feature)
        
        # y / lat
        for lat in lat_steps:
                # create geom and attributes
                vertices = []
                for lon in lon_steps_dense:
                    vertices.append(QgsPointXY(lon,lat))
                latlon = 'lat'
                deg = float(lat)
                lat_DDM, _ = utils.dd2ddm(lat, 0)
                label = opt_label(lat_DDM, self.interval_lat)
                geom = QgsGeometry.fromPolylineXY(vertices)
                
                # initialize line feature
                feature = QgsFeature(fields)
                
                # set geometry
                feature.setGeometry(geom)
                
                # set attributes
                feature.setAttribute('latlon', latlon)
                feature.setAttribute('deg', deg)
                feature.setAttribute('label', label)
                
                # append feature to features list
                if feature.hasGeometry() and feature.isValid():
                    features.append(feature)
        
        # write coverage features to sink
        feedback.pushConsoleInfo(self.tr('Writing features...'))
        sink.addFeatures(features, QgsFeatureSink.FastInsert)
        
        # make variables accessible for post processing
        self.output = dest_id
        
        result = {self.OUTPUT : self.output}
        
        return result

    def postProcessAlgorithm(self, context, feedback):  # noqa
        # get layer from source and context
        coord_grid_layer = QgsProcessingUtils.mapLayerFromString(self.output, context)
        
        # loading Cruise Tools Coordinate Grid layer style from QML style file
        feedback.pushConsoleInfo(self.tr('Loading style...'))
        coord_grid_layer.loadNamedStyle(self.style_coordinate_grid)
        
        # writing style to GPKG (or else)
        style_name = 'Cruise Tools Coordinate Grid'
        style_desc = 'Coordinate Grid style for QGIS Symbology from Cruise Tools plugin'
        
        feedback.pushConsoleInfo(self.tr('Writing style to output...\n'))
        coord_grid_layer.saveStyleToDatabase(name=style_name, description=style_desc, useAsDefault=True, uiFileContent=None)
        
        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Coordinate grid file created!\n'))
        
        result = {self.OUTPUT : self.output}
        
        return result
    
    def name(self):  # noqa
        return 'createcoordinategrid'

    def icon(self):  # noqa
        icon = QIcon(f'{self.plugin_dir}/icons/create_coordinate_grid.png')
        return icon

    def displayName(self):  # noqa
        return self.tr('Create Coordinate Grid')

    def group(self):  # noqa
        return self.tr('Vector')

    def groupId(self):  # noqa
        return 'vector'

    def tr(self, string):  # noqa
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):  # noqa
        doc = f'{self.plugin_dir}/doc/create_coordinate_grid.help'
        if not os.path.exists(doc):
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):  # noqa
        return CreateCoordinateGrid()
