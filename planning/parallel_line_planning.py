import os

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFeature,
    QgsGeometry,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterNumber,
    QgsProcessingParameterVectorLayer,
)

from qgis.PyQt.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon

from .planning import Planning
from .. import utils

class ParallelLinePlanning(QgsProcessingAlgorithm, Planning):
    """Parallel Line Planning."""

    # Processing parameters
    # inputs:
    INPUT = 'INPUT'
    SELECTED = 'SELECTED'
    OFFSET = 'OFFSET'
    SIDE = 'SIDE'
    NUMBER_OF_LINES = 'NUMBER_OF_LINES'
    # outputs:
    OUTPUT = 'OUTPUT'

    def __init__(self):
        """Initialize ParallelLinePlanning."""
        super(ParallelLinePlanning, self).__init__()
        
        # available sides to create parallels
        self.sides = [self.tr('Starboard / Right'),
                      self.tr('Port / Left')]
        
        # offset settings
        # self.join_style = Qgis.JoinStyle.JoinStyleMiter
        # try except since earlier versions don't support the new
        # JoinStyleMiter, even though the documentation says it...
        try:
            self.join_style = Qgis.JoinStyle.JoinStyleMiter
        except AttributeError:
            self.join_style = Qgis.JoinStyle.Miter
        
        # initialize default configuration
        self.initConfig()

    def initConfig(self):
        """Get default values from CruiseToolsConfig."""
        self.side = self.config.getint(self.module, 'side')
        self.offset = self.config.getint(self.module, 'offset')
        self.number_of_lines = self.config.getint(self.module, 'number_of_lines')

    def initAlgorithm(self, config=None):  # noqa
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                name=self.INPUT,
                description=self.tr('Input line planning layer'),
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.OFFSET,
                description=self.tr('Offset [meters]'),
                type=QgsProcessingParameterNumber.Integer,
                optional=False,
                defaultValue=self.offset,
                minValue=0,
                maxValue=100000)
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.SIDE,
                description=self.tr('Side'),
                options=self.sides,
                defaultValue=self.side,
                optional=False,
                allowMultiple=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.NUMBER_OF_LINES,
                description=self.tr('Number of lines'),
                type=QgsProcessingParameterNumber.Integer,
                optional=False,
                defaultValue=self.number_of_lines,
                minValue=1,
                maxValue=100)
        )

    def processAlgorithm(self, parameters, context, feedback):  # noqa
        # get input variables
        layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        offset = self.parameterAsInt(parameters, self.OFFSET, context)
        side = self.parameterAsInt(parameters, self.SIDE, context)
        number_of_lines = self.parameterAsInt(parameters, self.NUMBER_OF_LINES, context)
        
        # set new default values in config
        feedback.pushConsoleInfo(self.tr('Storing new default settings in config...'))
        self.config.set(self.module, 'offset', offset)
        self.config.set(self.module, 'side', side)
        self.config.set(self.module, 'number_of_lines', number_of_lines)
        
        # adjust offset depending on side
        # positive is left/port
        # negative is right/starboard
        if side == 0:
            offset = -offset
        
        # get source CRS
        crs_layer = layer.sourceCrs()
        
        # get project transform_context
        transform_context = context.transformContext()
        
        # get (selected) features
        features = layer.getFeatures()
        
        feedback.pushConsoleInfo(self.tr('Creating parallel features...'))
        
        # empty list for original features to be deleted
        # this is necessary to keep the original line in order with the parallels
        features_to_delete = []
        
        # empty list for parallel line features
        features_to_add = []
        
        for feature in features:
            # add feature to features_to_delete and features_to_add list
            features_to_delete.append(feature)
            features_to_add.append(feature)
            
            # get feature id
            id = feature.id()
            
            # get feature geometry
            geom = feature.geometry()
            
            # get the centroid of the feature
            centroid = geom.centroid()
            lat, lon = centroid.vertexAt(0).y(), centroid.vertexAt(0).x()
            
            # determine best fitting UTM zone
            crs_utm = self.get_UTM_zone(lat, lon)
            
            # create transformations
            trans_layer2utm = QgsCoordinateTransform(crs_layer, crs_utm, transform_context)
            trans_utm2layer = QgsCoordinateTransform(crs_utm, crs_layer, transform_context)
            
            # transform geometry to UTM
            geom.transform(trans_layer2utm)
            
            # get feature fields
            fields = feature.fields()
            
            # get feature attributes
            attributes = feature.attributes()
            
            # reverse swith to reverse every second line
            reverse = True
            
            # create parallel features
            for i in range(number_of_lines):
                # set offset
                feature_offset = (i + 1) * offset
                
                # create parallel geometry
                geom_parallel = geom.offsetCurve(distance=feature_offset, segments=1, joinStyle=self.join_style, miterLimit=2.0)
                
                # transform back to original CRS
                geom_parallel.transform(trans_utm2layer)
                
                # reverse every second vector direction to create lawn mower pattern
                if reverse:
                    geom_parallel = QgsGeometry(geom_parallel.constGet().reversed())
                
                # initialize new feature
                feature_parallel = QgsFeature(fields)
                
                # set feature attributes and geometry
                feature_parallel.setAttributes(attributes)
                feature_parallel.setGeometry(geom_parallel)
                
                # append to feature list
                features_to_add.append(feature_parallel)
                
                # flip reverse
                reverse = not reverse
        
        # set layer to edit mode
        if not layer.isEditable():
            layer.startEditing()
        
        # delete original features
        for feature in features_to_delete:
                layer.deleteFeature(feature.id())
        
        # add new features to layer
        layer.addFeatures(features_to_add)
        
        # update layer # commented out to keep layer in edit mode
        #layer.commitChanges()
        #layer.triggerRepaint()
        
        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Parallel lines have been planned!\n'))
        
        result = {self.OUTPUT : layer}
        
        return result

    def name(self):  # noqa
        return 'parallellineplanning'

    def icon(self):  # noqa
        icon = QIcon(f'{self.plugin_dir}/icons/parallel_line_planning.png')
        return icon
    
    def displayName(self):  # noqa
        return self.tr('Parallel Line Planning')

    def group(self):  # noqa
        return self.tr('Planning')

    def groupId(self):  # noqa
        return 'planning'

    def tr(self, string):  # noqa
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):  # noqa
        doc = f'{self.plugin_dir}/doc/parallel_line_planning.help'
        if not os.path.exists(doc):
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):  # noqa
        return ParallelLinePlanning()
