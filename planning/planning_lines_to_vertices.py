import os

from qgis.core import (
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingUtils,
    QgsWkbTypes)

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from PyQt5.QtGui import QIcon

from .planning import Planning
from .. import utils

class PlanningLinesToVertices(QgsProcessingAlgorithm, Planning):
    """Planning Lines To Vertices."""

    # Processing parameters
    # inputs:
    INPUT = 'INPUT'
    ADD_VERTEX_ID = 'ADD_VERTEX_ID'
    LATLON_DD = 'LATLON_DD'
    LATLON_DDM = 'LATLON_DDM'
    # outputs:
    OUTPUT = 'OUTPUT'

    def __init__(self):
        """Initialize PlanningLinesToVertices."""
        super(PlanningLinesToVertices, self).__init__()
        
        # style files for planning layer
        self.style_planning_lines_vertices = ':/plugins/cruisetools/styles/style_planning_lines_to_vertices.qml'
        
        # initialize default configuration
        self.initConfig()
        
    def initConfig(self):
        """Get default values from CruiseToolsConfig."""
        self.latlon_dd = self.config.getboolean(self.module, 'latlon_dd')
        self.latlon_ddm = self.config.getboolean(self.module, 'latlon_ddm')

    def initAlgorithm(self, config=None):  # noqa
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.INPUT,
                description=self.tr('Input Line Planning Layer'),
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.OUTPUT,
                description=self.tr('Planning Line Vertices'),
                type=QgsProcessing.TypeVectorLine,
                defaultValue=None,
                optional=False,
                createByDefault=True)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.ADD_VERTEX_ID,
                description=self.tr('Add Vertex ID as Suffix to Field "name" (format: "_001")'),
                optional=False,
                defaultValue=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.LATLON_DD,
                description=self.tr('Add Lat/Lon coordinates (DD) [EPSG:4326]'),
                optional=False,
                defaultValue=self.latlon_dd)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.LATLON_DDM,
                description=self.tr('Add Lat/Lon coordinates (DDM) [EPSG:4326]'),
                optional=False,
                defaultValue=self.latlon_ddm)
        )

    def processAlgorithm(self, parameters, context, feedback):  # noqa
        # get input variables
        source = self.parameterAsSource(parameters, self.INPUT, context)
        
        self.add_vertex_suffix = self.parameterAsBoolean(parameters, self.ADD_VERTEX_ID, context)
        self.latlon_dd = self.parameterAsBoolean(parameters, self.LATLON_DD, context)
        self.latlon_ddm = self.parameterAsBoolean(parameters, self.LATLON_DDM, context)
        
        # set new default values in config
        feedback.pushConsoleInfo(self.tr('Storing new default settings in config...'))
        self.config.set(self.module, 'latlon_dd', self.latlon_dd)
        self.config.set(self.module, 'latlon_ddm', self.latlon_ddm)
        
        # fields to be created (empty)
        feedback.pushConsoleInfo(self.tr('Creating attribute fields...'))
        fields = QgsFields()
        
        # fields from feature source
        source_fields = source.fields()
        
        # if source does not have fid field, create it in fields
        if 'fid' not in source_fields.names():
            fields.append(QgsField('fid', QVariant.Int, '', 4, 0))
        
        # add all fields from source to fields variable
        for field in source_fields:
            fields.append(field)
        
        # creating feature sink for vertices
        feedback.pushConsoleInfo(self.tr('Creating feature sink...'))
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               fields, QgsWkbTypes.Point, source.sourceCrs())
        
        # get features from source
        features = source.getFeatures()
        
        # get vertices from features
        vertices = self.lines_to_vertices(features, fields)
        
        # write vertex features to sink
        sink.addFeatures(vertices, QgsFeatureSink.FastInsert)
        
        # make variables accessible for post processing
        self.output = dest_id
        
        result = {self.OUTPUT : self.output}
        
        return result

    def postProcessAlgorithm(self, context, feedback):  # noqa
        # get layer from source and context
        planning_layer = QgsProcessingUtils.mapLayerFromString(self.output, context)
        
        # get project transformContext for ellipsoidal measurements
        transform_context = context.transformContext()
        
        # run the function from Vector base class
        feedback.pushConsoleInfo(self.tr('Adding coordinate attributes...'))
        error, result = self.write_point_coordinates(planning_layer, transform_context, self.latlon_dd, self.latlon_ddm, False, None)
        if error:
            feedback.reportError(self.tr(result), fatalError=True)
            return {}
        
        # loading Cruise Tools Planning style from QML style file
        feedback.pushConsoleInfo(self.tr('Loading style...'))
        planning_layer.loadNamedStyle(self.style_planning_lines_vertices)
        
        # writing style to GPKG (or else)
        style_name = 'Cruise Tools Planning Vertices'
        style_desc = 'Planning Vertices style for QGIS Symbology from Cruise Tools plugin'
        
        feedback.pushConsoleInfo(self.tr('Writing style to output...\n'))
        planning_layer.saveStyleToDatabase(name=style_name, description=style_desc, useAsDefault=True, uiFileContent=None)
        
        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Vertices file created!\n'))
        
        result = {self.OUTPUT : self.output}
        
        return result

    def name(self):  # noqa
        return 'planninglinestovertices'

    def icon(self):  # noqa
        icon = QIcon(f'{self.plugin_dir}/icons/planning_lines_to_vertices.png')
        return icon

    def displayName(self):  # noqa
        return self.tr('Planning Lines To Vertices')

    def group(self):  # noqa
        return self.tr('Planning')

    def groupId(self):  # noqa
        return 'planning'

    def tr(self, string):  # noqa
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):  # noqa
        doc = f'{self.plugin_dir}/doc/planning_lines_to_vertices.help'
        if not os.path.exists(doc):
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):  # noqa
        return PlanningLinesToVertices()
