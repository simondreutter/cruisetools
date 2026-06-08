from pathlib import Path

from qgis.core import QgsCoordinateTransform
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsFeatureRequest
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterField
from qgis.core import QgsProcessingParameterFolderDestination
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterString

from qgis.PyQt.QtCore import QCoreApplication, QMetaType
from qgis.PyQt.QtGui import QIcon

from .planning import Planning
from .. import utils


class ExportPointsToRTZ(QgsProcessingAlgorithm, Planning):
    """Export Points To RTZ"""

    # Processing parameters
    # inputs:
    INPUT = 'INPUT'
    ORDER_BY = 'ORDER_BY'
    # process:
    DUPLICATE_PRECISION = 6
    # outputs:
    RADIUS_FALLBACK = 'RADIUS_FALLBACK'
    ROUTE_NAME = 'ROUTE_NAME'
    CATALOG = 'CATALOG'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super(ExportPointsToRTZ, self).__init__()

        self.vertex_suffix = False

        # initialize default configuration
        self.initConfig()

    def initConfig(self):
        self.rtz_catalog = self.config.getint(self.module, 'rtz_catalog')
        self.radius_fallback = self.config.getint(self.module, 'radius_fallback')

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.INPUT,
                description=self.tr('Input point planning layer'),
                types=[QgsProcessing.SourceType.TypeVectorPoint],
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterField(
                name=self.ORDER_BY,
                description=self.tr('Order by'),
                parentLayerParameterName=self.INPUT,
                defaultValue='fid',
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.RADIUS_FALLBACK,
                description=self.tr('Turn radius [nm] (fallback)'),
                type=QgsProcessingParameterNumber.Type.Double,
                defaultValue=self.radius_fallback,
                minValue=0.0,
                maxValue=5.0,
                optional=False)
        )
        self.parameterDefinition(self.RADIUS_FALLBACK).setMetadata({
            'widget_wrapper': {'decimals': 2}
        })
        self.addParameter(
            QgsProcessingParameterString(
                name=self.ROUTE_NAME,
                description=self.tr('Route name'),
                defaultValue='Route',
                multiLine=False,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterString(
                name=self.CATALOG,
                description=self.tr('Catalog name'),
                defaultValue=self.rtz_catalog,
                multiLine=False,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                name=self.OUTPUT,
                description=self.tr('RTZ export directory'),
                createByDefault=False
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        # get input variables
        source = self.parameterAsSource(parameters, self.INPUT, context)
        order_by = self.parameterAsString(parameters, self.ORDER_BY, context)
        route_name = self.parameterAsString(parameters, self.ROUTE_NAME, context)
        rtz_catalog = self.parameterAsString(parameters, self.CATALOG, context)
        radius_fallback = self.parameterAsDouble(parameters, self.RADIUS_FALLBACK, context)
        output = self.parameterAsFileOutput(parameters, self.OUTPUT, context)

        # set new default values in config
        feedback.pushConsoleInfo(self.tr('Storing new default settings in config...'))
        self.config.set(self.module, 'rtz_catalog', rtz_catalog)
        self.config.set(self.module, 'radius_fallback', radius_fallback)

        # coordinate transformation
        trans = QgsCoordinateTransform(
            source.sourceCrs(),
            QgsCoordinateReferenceSystem('EPSG:4326'),
            context.transformContext()
        )

        # make output directory
        feedback.pushConsoleInfo(self.tr('Creating output directory...'))
        # sanitize catalog name
        rtz_catalog = utils.sanitize_filename(rtz_catalog)
        output_dir = Path(output) / 'RouteExchange' / rtz_catalog
        output_dir.mkdir(parents=True, exist_ok=True)

        # sanitize route name
        route_name = utils.sanitize_filename(route_name)

        # output route file
        route_file = output_dir / f'{route_name}.rtz'
        if route_file.is_file():
            feedback.pushConsoleInfo(self.tr(f'Route file {route_name}.rtz already exists!'))
            feedback.pushConsoleInfo(self.tr(f'Backing up existing file...'))
            utils.backup_file(route_file)

        # empty list of points
        table = []

        # get features from source
        feedback.pushConsoleInfo(self.tr('Processing point features...'))
        request = QgsFeatureRequest()
        request.addOrderBy(order_by, True)  # True for ascending, False for descending
        features = source.getFeatures(request)

        # iterate over point features
        for feature in features:
            # get fields and attributes
            fields = feature.fields().names()
            attributes = feature.attributes()

            # create field-attribute dict
            point_dict = dict(zip(fields, attributes))

            # extract Latitude and Longitude coordinates (EPSG:4326)
            geom = feature.geometry().asPoint()
            geom4326 = trans.transform(geom)

            lat = geom4326.y()
            lon = geom4326.x()

            if not (-90 <= lat <= 90):
                raise ValueError(f'Invalid latitude {lat}')
            if not (-180 <= lon <= 180):
                raise ValueError(f'Invalid longitude {lon}')

            # add coordinates to point dict
            point_dict['lat_DD'] = lat
            point_dict['lon_DD'] = lon

            # append point to table
            table.append(point_dict)

        # export points
        error, result = self.export_rtz(table=table,
                                        output=route_file,
                                        line=False,
                                        duplicate_precision=self.DUPLICATE_PRECISION,
                                        radius_fallback=radius_fallback)
        if error:
            feedback.reportError(self.tr(result), fatalError=True)
            return {}

        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Export file created!'))

        return {self.OUTPUT: output}

    def name(self):
        return 'exportpointstortz'

    def icon(self):
        return QIcon(str(self.plugin_dir / 'icons' / 'export_points_to_rtz.png'))

    def displayName(self):
        return self.tr('Export Points To RTZ')

    def group(self):
        return self.tr('Planning')

    def groupId(self):
        return 'planning'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        doc = Path(self.plugin_dir) / 'doc' / 'export_points_to_rtz.help'
        if not doc.is_file():
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return ExportPointsToRTZ()
