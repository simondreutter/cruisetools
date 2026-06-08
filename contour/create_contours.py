from pathlib import Path

import processing

from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingParameterBand
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterVectorDestination
from qgis.core import QgsProcessingUtils

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon

from .contour import Contour
from .. import utils
from .. import vector


class CreateContours(QgsProcessingAlgorithm, Contour):
    """Create Contours."""

    # Processing parameters
    # inputs:
    INPUT = 'INPUT'
    BAND = 'BAND'
    Z_POS_DOWN = 'Z_POS_DOWN'
    INTERVAL = 'INTERVAL'
    # outputs:
    OUTPUT = 'OUTPUT'

    def __init__(self):
        """Initialize CreateContours."""
        super(CreateContours, self).__init__()
        self.initConfig()

        # style file for contour layer
        self.style_contours = self.plugin_dir / 'styles' / 'style_contours.qml'

    def initConfig(self):
        """Get default values from CruiseToolsConfig."""
        self.interval = self.config.getint(self.module, 'interval')

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                name=self.INPUT,
                description=self.tr('Input raster layer'),
                defaultValue=None,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBand(
                name=self.BAND,
                description=self.tr('Band number'),
                defaultValue=1,
                parentLayerParameterName=self.INPUT,
                optional=False,
                allowMultiple=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.Z_POS_DOWN,
                description=self.tr('Raster Z positive down'),
                optional=False,
                defaultValue=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.INTERVAL,
                description=self.tr('Contour interval'),
                type=QgsProcessingParameterNumber.Type.Integer,
                optional=False,
                defaultValue=self.interval,
                minValue=0,
                maxValue=12000)
        )
        self.addParameter(
            QgsProcessingParameterVectorDestination(
                name=self.OUTPUT,
                description=self.tr('Contours'),
                defaultValue=None,
                optional=False,
                createByDefault=False)
        )

    def processAlgorithm(self, parameters, context, feedback):
        # get input variables
        raster_layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        band_number = self.parameterAsInt(parameters, self.BAND, context)
        z_pos_down = self.parameterAsBoolean(parameters, self.Z_POS_DOWN, context)
        interval = self.parameterAsInt(parameters, self.INTERVAL, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        # set new default values in config
        feedback.pushConsoleInfo(self.tr('Storing new default settings in config...'))
        self.config.set(self.module, 'interval', interval)

        # 5% done
        feedback.setProgress(5)

        # get output file extension (.gpkg or .shp)
        base_path, base_name, ext = utils.get_info_from_path(output)

        # get CRS from raster file (for some reason gdal:contour is assigning a false CRS otherwise...)
        crs = raster_layer.crs()

        # get temporary folder
        tmp_folder = Path(QgsProcessingUtils.tempFolder())

        # temp file for raw contours
        contours_raw = tmp_folder / f'contours_raw.{ext}'

        # parameters for contour algorithm
        params_contour = {'INPUT': raster_layer,
                          'BAND': band_number,
                          'INTERVAL': interval,
                          'FIELD_NAME': 'ELEV',
                          'CREATE_3D': True,
                          'IGNORE_NODATA': False,
                          'NODATA': raster_layer.dataProvider().sourceNoDataValue(band_number),
                          'OFFSET': 0,
                          'OUTPUT': str(contours_raw)}

        # create raw contours
        feedback.pushConsoleInfo(self.tr(f'Creating raw contours with {interval} m interval...'))
        processing.run('gdal:contour', params_contour)

        # 35% done
        feedback.setProgress(35)

        # temp file for raw contours
        contours_smooth = tmp_folder / f'contours_smooth.{ext}'

        # parameters for smoothing
        params_smooth = {'INPUT': str(contours_raw),
                         'ITERATIONS': 3,
                         'MAX_ANGLE': 180,
                         'OFFSET': 0.25,
                         'OUTPUT': str(contours_smooth)}

        # smooth contours
        feedback.pushConsoleInfo(self.tr('Smoothing contours...'))
        processing.run('native:smoothgeometry', params_smooth)

        # 55% done
        feedback.setProgress(55)

        # parameters for fixing projection
        params_prj = {'INPUT': str(contours_smooth),
                      'CRS': crs,
                      'OUTPUT': output}

        # fix projection
        feedback.pushConsoleInfo(self.tr('Fixing CRS...'))
        processing.run('native:reprojectlayer', params_prj)

        # 60% done
        feedback.setProgress(60)

        # make variables accessible for post-processing
        self.output = output
        self.z_pos_down = z_pos_down

        result = {self.OUTPUT: output}

        return result

    def postProcessAlgorithm(self, context, feedback):
        # get layer from source and context
        contours_layer = QgsProcessingUtils.mapLayerFromString(self.output, context)

        # vector modifyer from Vector base class
        vector_mod = vector.Vector()

        # to adjust labels, swap vectors (except if grid is Z positive down)
        if not self.z_pos_down:
            feedback.pushConsoleInfo(self.tr('Swapping contour direction...'))
            vector_mod.swap_vectors(contours_layer, selected=False)

        # 70% done
        feedback.setProgress(70)

        # adding length attribute with write_line_length for length filtering
        feedback.pushConsoleInfo(self.tr('Adding length attributes...'))
        ellipsoid = context.project().crs().ellipsoidAcronym()
        transform_context = context.project().transformContext()
        vector_mod.write_line_length(contours_layer, ellipsoid, transform_context, m=True)

        # 98% done
        feedback.setProgress(98)

        # loading Cruise Tools Contours style from QML style file
        feedback.pushConsoleInfo(self.tr('Loading style...'))
        contours_layer.loadNamedStyle(str(self.style_contours))

        # writing style to GPKG (or else)
        style_name = 'Cruise Tools Contours'
        style_desc = 'Contour style for QGIS Symbology and Labels from Cruise Tools plugin'

        feedback.pushConsoleInfo(self.tr('Writing style to output...\n'))
        contours_layer.saveStyleToDatabaseV2(name=style_name,
                                             description=style_desc,
                                             useAsDefault=True,
                                             uiFileContent=None)

        contours_layer.triggerRepaint()

        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Contours have been computed!\n'))

        result = {self.OUTPUT: self.output}

        return result

    def name(self):
        return 'createcontours'

    def icon(self):
        return QIcon(str(self.plugin_dir / 'icons' / 'create_contours.png'))

    def displayName(self):
        return self.tr('Create Contours')

    def group(self):
        return self.tr('Contour')

    def groupId(self):
        return 'contour'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        doc = Path(self.plugin_dir) / 'doc' / 'create_contours.help'
        if not doc.is_file():
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return CreateContours()
