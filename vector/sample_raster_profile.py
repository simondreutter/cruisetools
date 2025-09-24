from math import floor
import os

from qgis.core import QgsCoordinateTransform
from qgis.core import QgsDistanceArea
from qgis.core import QgsFeature
from qgis.core import QgsFeatureSink
from qgis.core import QgsField
from qgis.core import QgsFields
from qgis.core import QgsGeometry
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingException
from qgis.core import QgsProcessingParameterBand
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterVectorLayer
from qgis.core import QgsProject
from qgis.core import QgsWkbTypes

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from PyQt5.QtGui import QIcon, QColor

from .vector import Vector
from .. import utils


class SampleRasterProfile(QgsProcessingAlgorithm, Vector):
    """Sample Raster Profile."""

    # Processing parameters
    # inputs:
    INPUT_LINE = 'INPUT_LINE'
    SELECTED = 'SELECTED'
    DISTANCE = 'DISTANCE'
    INPUT_RASTER = 'INPUT_RASTER'
    BAND = 'BAND'
    # outputs:
    OUTPUT = 'OUTPUT'

    def __init__(self):
        """Initialize SampleRasterProfile."""
        super(SampleRasterProfile, self).__init__()

        # initialize default configuration
        self.initConfig()

    def initConfig(self):
        """Get default values from CruiseToolsConfig."""
        self.distance = self.config.getint(self.module, 'distance')
        self.raster_layer_name = self.config.getint(self.module, 'raster_layer')


    def initAlgorithm(self, config=None):  # noqa
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                name=self.INPUT_LINE,
                description=self.tr('Input line vector layer'),
                types=[QgsProcessing.TypeVectorLine],
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
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.DISTANCE,
                description=self.tr('Sample distance [meters]'),
                type=QgsProcessingParameterNumber.Integer,
                optional=True,
                defaultValue=self.distance,
                minValue=10)
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
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.OUTPUT,
                description=self.tr('Profile samples'),
                type=QgsProcessing.TypeVectorPoint,
                defaultValue=None,
                optional=False,
                createByDefault=True)
        )

    def processAlgorithm(self, parameters, context, feedback):  # noqa
        # get input variables as self.* for use in post-processing
        self.vector_layer = self.parameterAsVectorLayer(parameters, self.INPUT_LINE, context)
        selected = self.parameterAsBoolean(parameters, self.SELECTED, context)
        distance = self.parameterAsInt(parameters, self.DISTANCE, context)
        raster_layer = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        band_number = self.parameterAsInt(parameters, self.BAND, context)

        # set new default values in config
        feedback.pushConsoleInfo(self.tr('Storing new default settings in config...'))
        self.config.set(self.module, 'distance', distance)
        self.config.set(self.module, 'raster_layer', raster_layer.name())

        # catch undefined project CRS
        project_crs = QgsProject.instance().crs()
        if not project_crs.isValid() or project_crs.authid() == "":
            raise QgsProcessingException(
                self.tr("Project CRS is undefined. Please set a valid project CRS before running this tool.")
            )

        # get project transformContext for ellipsoidal measurements
        transform_context = context.transformContext()

        # get crs's
        crs_line = self.vector_layer.sourceCrs()
        crs_raster = raster_layer.crs()

        # create transformations for later
        trans_line2raster = QgsCoordinateTransform(crs_line, crs_raster, transform_context)

        # set fields and attributes
        reserved = {"fid", "ogc_fid", "id"}

        # line fid
        fields = QgsFields()
        fields.append(QgsField('line_fid', QVariant.Int))

        # add all fields from source to new fields
        for field in self.vector_layer.fields():
            if field.name().lower() in reserved:
                continue  # skip reserved fid-like fields
            fields.append(field)

        # sanitize name and create raster field
        self.raster_value_field_name = raster_layer.name().replace(' ', '_')
        raster_value_field = self.raster_band_field(raster_layer, band_number, self.raster_value_field_name)
        fields.append(raster_value_field)

        # creating feature sink
        feedback.pushConsoleInfo(self.tr('Creating feature sink...'))
        (sink, dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT, context, fields, QgsWkbTypes.Point, self.vector_layer.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        # set up distance calculator (always in meters)
        da = QgsDistanceArea()
        da.setSourceCrs(crs_line, transform_context)
        da.setEllipsoid(QgsProject.instance().ellipsoid())

        # get all features
        features = self.get_features(self.vector_layer, selected=selected)

        feedback.pushConsoleInfo(self.tr('Sampling raster points...'))
        for feature in features:
            # get geometry of feature
            geom = feature.geometry()
            if not geom:
                continue

            # total length in meters (ellipsoidal)
            length = da.measureLength(geom)
            num_steps = int(floor(length / distance))

            for i in range(num_steps + 1):
                d_meters = i * distance
                frac = d_meters / length
                point = geom.interpolate(frac * geom.length()).asPoint()

                if not point:
                    continue

                # transform to raster CRS for sampling
                point_raster_crs = trans_line2raster.transform(point)

                # sample raster
                raster_value, no_error = raster_layer.dataProvider().sample(point_raster_crs, band_number)

                # check if valid depth was sampled, otherwise set to NULL
                if not no_error:
                    raster_value = None

                # create feature
                out_feat = QgsFeature(fields)
                out_feat.setGeometry(QgsGeometry.fromPointXY(point))

                # set attributes from line feature
                attrs = [feature.id()]
                attrs += [feature[field.name()] for field in self.vector_layer.fields()
                          if field.name().lower() not in reserved]
                attrs += [raster_value]
                out_feat.setAttributes(attrs)

                # add feature to sink
                sink.addFeature(out_feat, QgsFeatureSink.FastInsert)

        # make variables accessible for post-processing
        self.output = dest_id

        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Profiles are sampled!\n'))

        result = {self.OUTPUT: self.output}

        return result

    def name(self):  # noqa
        return 'samplerasterprofile'

    def icon(self):  # noqa
        icon = QIcon(f'{self.plugin_dir}/icons/sample_raster_profile.png')
        return icon

    def displayName(self):  # noqa
        return self.tr('Sample Raster Profile')

    def group(self):  # noqa
        return self.tr('Vector')

    def groupId(self):  # noqa
        return 'vector'

    def tr(self, string):  # noqa
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):  # noqa
        doc = f'{self.plugin_dir}/doc/sample_raster_profile.help'
        if not os.path.exists(doc):
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):  # noqa
        return SampleRasterProfile()
