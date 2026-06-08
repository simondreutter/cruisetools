from pathlib import Path

from qgis.core import QgsCoordinateTransform
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsField
from qgis.core import QgsFields
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterFileDestination
from qgis.core import QgsWkbTypes

from qgis.PyQt.QtCore import QCoreApplication, QMetaType
from qgis.PyQt.QtGui import QIcon

from .planning import Planning
from .. import utils


class ExportToCSV(QgsProcessingAlgorithm, Planning):
    """Export To CSV"""

    # Processing parameters
    # inputs:
    INPUT = 'INPUT'
    # process:
    DUPLICATE_PRECISION = 6
    # outputs:
    RADIUS_FALLBACK = 'RADIUS_FALLBACK'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super(ExportToCSV, self).__init__()

        self.vertex_suffix = True

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.INPUT,
                description=self.tr('Input planning layer'),
                types=[QgsProcessing.SourceType.TypeVectorPoint, QgsProcessing.SourceType.TypeVectorLine],
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                name=self.OUTPUT,
                description=self.tr('CSV export'),
                fileFilter='CSV (*.csv)',
                createByDefault=False
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        # get input variables
        source = self.parameterAsSource(parameters, self.INPUT, context)
        output = self.parameterAsFileOutput(parameters, self.OUTPUT, context)

        # coordinate transformation
        trans = QgsCoordinateTransform(
            source.sourceCrs(),
            QgsCoordinateReferenceSystem('EPSG:4326'),
            context.transformContext()
        )

        # get geometry type of input layer
        geom_type = QgsWkbTypes.geometryType(source.wkbType())

        if geom_type == QgsWkbTypes.GeometryType.LineGeometry:
            # fields to be created (empty)
            fields = QgsFields()

            # fields from source
            source_fields = source.fields()

            # if source does not have fid field, create it in fields
            if 'fid' not in source_fields.names():
                fields.append(QgsField('fid', QMetaType.Type.Int, '', 4, 0))

            # add all fields from source to fields variable
            for field in source_fields:
                fields.append(field)

            # get line features
            features = source.getFeatures()

            # get line vertices
            points = self.lines_to_vertices(features, fields)
        elif geom_type == QgsWkbTypes.GeometryType.PointGeometry:
            points = source.getFeatures()
        else:
            feedback.reportError(self.tr('Unknown Geometry WKB Type'), fatalError=True)
            return {}

        # empty list of points
        table = []

        # preprocess points
        for point in points:
            # get fields and attributes
            point_fields = point.fields().names()
            point_attributes = point.attributes()

            # create field-attribute dict
            point_dict = dict(zip(point_fields, point_attributes))

            # extract Latitude and Longitude coordinates (EPSG:4326)
            geom = point.geometry().asPoint()
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

        # export lines
        error, result = self.export_csv(table=table,
                                        output=output)
        if error:
            feedback.reportError(self.tr(result), fatalError=True)
            return {}

        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Export file created!'))

        return {self.OUTPUT: output}

    def name(self):
        return 'exporttocsv'

    def icon(self):
        return QIcon(str(self.plugin_dir / 'icons' / 'export_to_csv.png'))

    def displayName(self):
        return self.tr('Export To CSV')

    def group(self):
        return self.tr('Planning')

    def groupId(self):
        return 'planning'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        doc = Path(self.plugin_dir) / 'doc' / 'export_to_csv.help'
        if not doc.is_file():
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return ExportToCSV()
