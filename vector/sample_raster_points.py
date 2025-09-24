import os

from qgis.core import QgsCoordinateTransform
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingParameterBand
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProject
from qgis.core import QgsWkbTypes

from qgis.PyQt.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon

from .vector import Vector
from .. import utils


class SampleRasterPoints(QgsProcessingAlgorithm, Vector):
    """Sample Raster Points."""

    # Processing parameters
    # inputs:
    INPUT_POINT = 'INPUT_POINT'
    SELECTED = 'SELECTED'
    INPUT_RASTER = 'INPUT_RASTER'
    BAND = 'BAND'
    # outputs:
    OUTPUT = 'OUTPUT'

    def __init__(self):
        """Initialize SampleRasterPoints."""
        super(SampleRasterPoints, self).__init__()

        # initialize default configuration
        self.initConfig()

    def initConfig(self):
        """Get default values from CruiseToolsConfig."""
        self.raster_layer_name = self.config.getint(self.module, 'raster_layer')


    def initAlgorithm(self, config=None):  # noqa
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                name=self.INPUT_POINT,
                description=self.tr('Input point vector layer'),
                types=[QgsProcessing.TypeVectorPoint],
                defaultValue=None,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.SELECTED,
                description=self.tr('Sample only selected features'),
                optional=False,
                defaultValue=False)
        )
        raster_layers = [lyr for lyr in QgsProject.instance().mapLayers().values() if lyr.type() == 1]
        raster_layer_names = [r.name() for r in raster_layers]
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                name=self.INPUT_RASTER,
                description=self.tr('Input raster layer'),
                defaultValue=(
                    self.raster_layer_name
                    if self.raster_layer_name in raster_layer_names
                    else None
                ),
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBand(
                name=self.BAND,
                description=self.tr('Band number'),
                defaultValue=1,
                parentLayerParameterName=self.INPUT_RASTER,
                optional=False,
                allowMultiple=False)
        )

    def processAlgorithm(self, parameters, context, feedback):  # noqa
        # get input variables as self.* for use in post-processing
        self.vector_layer = self.parameterAsVectorLayer(parameters, self.INPUT_POINT, context)
        self.selected = self.parameterAsBoolean(parameters, self.SELECTED, context)
        self.raster_layer = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        self.band_number = self.parameterAsInt(parameters, self.BAND, context)

        # set new default values in config
        feedback.pushConsoleInfo(self.tr('Storing new default settings in config...'))
        self.config.set(self.module, 'raster_layer', self.raster_layer.name())

        result = {}

        return result

    def postProcessAlgorithm(self, context, feedback):  # noqa
        # layer in-place editing is not working very well in the processAlgorithm
        # therefore it was moved here to post-processing

        # geometry type
        feedback.pushConsoleInfo(self.tr('Checking input geometry...'))
        geom_type = QgsWkbTypes.geometryType(self.vector_layer.wkbType())
        multi_type = QgsWkbTypes.isMultiType(self.vector_layer.wkbType())
        if (geom_type != 0) or multi_type:
            error = "This didn't work. Is your layer a MULTIPOINT layer? If so, convert it to POINT, because only POINT layers are supported."
            feedback.reportError(self.tr(error), fatalError=True)
            return {}

        # get project transformContext for ellipsoidal measurements
        transform_context = context.transformContext()

        # sanitize and set field name
        raster_value_field_name = self.raster_layer.name()
        raster_value_field_name = raster_value_field_name.replace(' ', '_')

        # get crs's
        crs_point = self.vector_layer.sourceCrs()
        crs_raster = self.raster_layer.crs()

        # create transformations for later
        trans_point2raster = QgsCoordinateTransform(crs_point, crs_raster, transform_context)

        # with edit(layer):

        if not self.vector_layer.isEditable():
            self.vector_layer.startEditing()

        # delete fields previously created by Cruise Tools
        feedback.pushConsoleInfo(self.tr('Removing old sample field...'))
        self.delete_fields_by_prefix(self.vector_layer, raster_value_field_name)

        # get raster dtype as mapped QVariant
        feedback.pushConsoleInfo(self.tr('Creating new sample field...'))
        raster_value_field = self.raster_band_field(self.raster_layer, self.band_number, raster_value_field_name)

        # create field for raster value
        self.vector_layer.addAttribute(raster_value_field)

        # update attribute table fields
        self.vector_layer.updateFields()

        # get all features
        features = self.get_features(self.vector_layer, selected=self.selected)

        feedback.pushConsoleInfo(self.tr('Sampling raster points...'))
        for feature in features:
            # get geometry of feature
            point = feature.geometry().asPoint()

            # transform geometry to EPSG:4326 CRS
            point_raster_crs = trans_point2raster.transform(point)

            # sample raster value
            raster_value, no_error = self.raster_layer.dataProvider().sample(point_raster_crs, self.band_number)

            # check if valid depth was sampled, otherwise set to NULL
            if not no_error:
                raster_value = None

            # set attribute value
            feature.setAttribute(feature.fieldNameIndex(raster_value_field_name), raster_value)

            # update attribute table
            self.vector_layer.updateFeature(feature)

        self.vector_layer.commitChanges()

        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Points are sampled!\n'))

        result = {self.OUTPUT: self.vector_layer}

        return result

    def name(self):  # noqa
        return 'samplerasterpoints'

    def icon(self):  # noqa
        icon = QIcon(f'{self.plugin_dir}/icons/sample_raster_points.png')
        return icon

    def displayName(self):  # noqa
        return self.tr('Sample Raster Points')

    def group(self):  # noqa
        return self.tr('Vector')

    def groupId(self):  # noqa
        return 'vector'

    def tr(self, string):  # noqa
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):  # noqa
        doc = f'{self.plugin_dir}/doc/sample_raster_points.help'
        if not os.path.exists(doc):
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):  # noqa
        return SampleRasterPoints()
