from pathlib import Path

import processing

from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsProcessingParameterDefinition
from qgis.core import QgsProcessingParameterEnum
from qgis.core import QgsProcessingParameterRasterDestination
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingUtils
from qgis.core import QgsRasterBandStats
from qgis.core import QgsRasterFileWriter
from qgis.core import QgsRasterLayer
from qgis.core import QgsRasterPipe

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon

from .bathymetry import Bathymetry
from .. import utils


class ExportShadedBathymetry(QgsProcessingAlgorithm, Bathymetry):
    """Export Shaded Bathymetry."""

    # Processing parameters
    # inputs:
    INPUT = 'INPUT'
    OPTIONS = 'OPTIONS'
    SHADER = 'SHADER'
    Z_POS_DOWN = 'Z_POS_DOWN'
    ALPHA = 'ALPHA'
    # outputs:
    OUTPUT = 'OUTPUT'

    def __init__(self):
        """Initialize ExportShadedBathymetry."""
        super(ExportShadedBathymetry, self).__init__()

        # available shading methods
        self.shaders = [self.tr('Hillshade'),
                        self.tr('Slope'),
                        self.tr('Combined'),
                        self.tr('Multidirectional')]

        # default extension for temporary files
        self.ext = 'tif'

        self.azimuth = 315.0
        self.altitude = 45.0

        # set default vertical exaggeration
        self.hillshade_z_factor = 10.0
        self.slope_z_factor = 5.0

        # initialize default configuration
        self.initConfig()

    def initConfig(self):
        """Get default values from CruiseToolsConfig."""
        self.shader = self.config.get(self.module, 'shader')
        self.alpha = self.config.get(self.module, 'alpha')
        self.options = self.config.get(self.module, 'options')

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                name=self.INPUT,
                description=self.tr('Input raster layer'),
                defaultValue=None,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.Z_POS_DOWN,
                description=self.tr('Raster Z positive down'),
                optional=False,
                defaultValue=False)
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.SHADER,
                description=self.tr('Shader'),
                options=self.shaders,
                defaultValue=self.shader,
                optional=False,
                allowMultiple=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.ALPHA,
                description=self.tr('Add Alpha channel'),
                optional=False,
                defaultValue=self.alpha)
        )
        options_param = QgsProcessingParameterString(
            name=self.OPTIONS,
            description=self.tr('Additional creation options (e.g., COMPRESS=DEFLATE|PREDICTOR=2|TILED=YES)'),
            defaultValue=self.options,
            optional=True
        )
        options_param.setFlags(options_param.flags() | QgsProcessingParameterDefinition.Flag.FlagAdvanced)
        self.addParameter(options_param)
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                name=self.OUTPUT,
                description=self.tr('Shaded raster'),
                defaultValue=None,
                optional=False,
                createByDefault=True)
        )

    def processAlgorithm(self, parameters, context, feedback):
        # get input variables
        raster_layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        shader = self.parameterAsEnum(parameters, self.SHADER, context)
        options = self.parameterAsString(parameters, self.OPTIONS, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        z_pos_down = self.parameterAsBoolean(parameters, self.Z_POS_DOWN, context)
        alpha = self.parameterAsBoolean(parameters, self.ALPHA, context)

        feedback.pushConsoleInfo(self.tr(f'Shader: {self.shaders[shader]}\n'))

        # set new default values in config
        feedback.pushConsoleInfo(self.tr('Storing new default settings in config...'))
        self.config.set(self.module, 'shader', shader)
        self.config.set(self.module, 'alpha', alpha)
        self.config.set(self.module, 'options', options)

        # create switches for shader
        hillshade, slope, combo, multi = False, False, False, False

        # set settings by shader
        if shader == 0:
            hillshade = True
        elif shader == 1:
            slope = True
        elif shader == 2:
            combo = True
        elif shader == 3:
            multi = True

        # create temporary folder
        tmp_folder = Path(QgsProcessingUtils.tempFolder())

        # render selected layer with defined symbology as rgb raster
        feedback.pushConsoleInfo(self.tr('Rendering layer to RGB...'))
        rgb_file = tmp_folder / f'rgb.{self.ext}'
        error, result = self.create_rgb(raster_layer, rgb_file)
        if error:
            feedback.reportError(self.tr(result), fatalError=True)
            return {}

        # 20% done
        if feedback.isCanceled():
            return {}
        feedback.setProgress(20)

        # get crs from layer
        crs_raster = raster_layer.crs()

        # get scale for vertical units
        scale = self.get_scale(crs_raster)

        # shading file path
        shading_file = tmp_folder / f'shading_file.{self.ext}'

        # create shading file
        if hillshade or combo or multi:
            # create hillshade
            feedback.pushConsoleInfo(self.tr('Creating shading grid...'))
            # if raster is z positive down flip illumination direction
            if z_pos_down:
                self.azimuth = (self.azimuth - 180.) % 360.
            shading_file = self.hillshade(raster_layer,
                                          self.hillshade_z_factor,
                                          scale, self.azimuth,
                                          self.altitude,
                                          combo,
                                          multi,
                                          shading_file,
                                          options)

        elif slope:
            # create slope
            feedback.pushConsoleInfo(self.tr('Creating shading grid...'))
            shading_file = self.slopeshade(raster_layer,
                                           self.slope_z_factor,
                                           scale,
                                           shading_file,
                                           options)

        # 70% done
        if feedback.isCanceled():
            return {}
        feedback.setProgress(70)

        # shading computation
        feedback.pushConsoleInfo(self.tr('Calculating output raster...'))
        syntax = 'uint8(((A/255.)*(((B*0.5)+(255.*0.5))/255.))*255)'
        output = self.shade(rgb_file,
                            shading_file,
                            syntax,
                            crs_raster,
                            output,
                            options,
                            alpha)

        # 99% done
        if feedback.isCanceled():
            return {}
        feedback.setProgress(99)

        # remove temp files
        feedback.pushConsoleInfo(self.tr('Deleting temporary files...\n'))
        for file in [rgb_file, shading_file]:
            if file.exists():
                file.unlink()

        # 100% done
        if feedback.isCanceled():
            return {}
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Shaded bathymetry file is created!\n'))

        result = {self.OUTPUT: str(output)}

        return result

    def create_rgb(self, raster_layer, output):
        """Render and write RGB file.

        Parameters
        ----------
        raster_layer : QgsRasterLayer
            input raster layer with singleband pseudocolor
        output : pathlib.Path or str
            output file path

        Returns
        -------
        error : boolean
            0/1 - no error/error
        result : pathlib.Path or str
            output or error msg if error == 1
    
        """
        # get raster_layer properties
        extent = raster_layer.extent()
        width, height = raster_layer.width(), raster_layer.height()
        renderer = raster_layer.renderer()
        provider = raster_layer.dataProvider()
        crs_raster = raster_layer.crs()

        # create pipe for export
        pipe = QgsRasterPipe()
        pipe.set(provider.clone())
        pipe.set(renderer.clone())

        # create FileWriter and write file
        fwriter = QgsRasterFileWriter(str(output))
        error = fwriter.writeRaster(pipe, width, height, extent, crs_raster)
        if error != fwriter.NoError:
            return 1, 'RGB file could not be rendered!'

        return 0, Path(output)

    def get_scale(self, crs):
        """Get scale for vertical units in grid.

        Parameters
        ----------
        crs : QgsCoordinateReferenceSystem
            input CRS

        Returns
        -------
        scale : float
            vertical scale

        """
        # if the grid is geographic, vertical will be interpreted as degree
        # hence the scale needs to be 0.000009.
        if crs.isGeographic():
            scale = 10 ** 7 / 90  # 111111.111...
        # otherwise it's considered in meters and the scale is 1.
        else:
            scale = 1.0

        return scale

    def hillshade(self, input, z_factor, scale, azimuth, altitude, combined, multidirectional, output, options):
        """Create hillshade grid from raster input.

        Parameters
        ----------
        input : pathlib.Path or str
            file path to raster DEM
        z_factor : float
            vertical exaggeration
        scale : float
            1.0 for meters and 111111.111 for geographic raster
        azimuth : float
            direction angle of illumination
        altitude : float
            altitude angle of illumination
        combined : boolean
            combined shading (mutually exclusive with multidirectional)
        multidirectional : boolean
            multidirectional shading (mutually exclusive with combined)
        output : pathlib.Path or str
            file path to hillshade raster output
        options : str
            GDAL create options

        Returns
        -------
        output : pathlib.Path
            file path to hillshade raster output

        """
        # hillshade parameters
        params = {'INPUT': input,
                  'BAND': 1,
                  'Z_FACTOR': z_factor,
                  'SCALE': scale,
                  'AZIMUTH': azimuth,
                  'ALTITUDE': altitude,
                  'COMPUTE_EDGES': True,
                  'COMBINED': combined,
                  'MULTIDIRECTIONAL': multidirectional,
                  'OPTIONS': options,
                  'OUTPUT': str(output)}

        # run hillshade
        processing.run('gdal:hillshade', params)

        return Path(output)

    def slopeshade(self, input, z_factor, scale, output, options):
        """Create slope shading grid from raster input.

        Parameters
        ----------
        input : pathlib.Path or str
            file path to raster DEM
        z_factor : float
            vertical exaggeration
        scale : float
            1.0 for meters and 111111.111 for geographic raster
        output : pathlib.Path or str
            file path to slope raster output
        options : str
            GDAL create options

        Returns
        -------
        output : pathlib.Path
            file path to slope raster output

        """
        # create temporary folder
        tmp_folder = Path(QgsProcessingUtils.tempFolder())
        tmp_slope = tmp_folder / f'slope.{self.ext}'
        tmp_stretch = tmp_folder / f'stretch.{self.ext}'

        # slope parameters
        params = {'INPUT': input,
                  'BAND': 1,
                  'SCALE': scale / z_factor,
                  'COMPUTE_EDGES': True,
                  'OPTIONS': options,
                  'OUTPUT': str(tmp_slope)}

        # run slope
        processing.run('gdal:slope', params)

        # stretch slope to min-max
        # min max values (byte)
        dmin = 1.
        dmax = 254.

        # create raster layer from input to get stats
        raster_layer = QgsRasterLayer(str(tmp_slope), 'tmp', 'gdal')
        extent = raster_layer.extent()
        provider = raster_layer.dataProvider()

        # get stats
        stats = provider.bandStatistics(1, QgsRasterBandStats.Stats.All, extent, 0)
        smin = stats.minimumValue
        smax = stats.maximumValue

        # translate parameters
        params = {'INPUT': str(tmp_slope),
                  'NO_DATA': 0,
                  'RTYPE': 0,
                  'OPTIONS': options,
                  'EXTRA': '-scale {} {} {} {} -r bilinear'.format(smin, smax, dmin, dmax),
                  'OUTPUT': str(tmp_stretch)}

        # run translate
        processing.run('gdal:translate', params)

        # dereference raster layer
        raster_layer = None

        # invert slope
        # raster calculator parameters
        params = {'INPUT_A': str(tmp_stretch),
                  'BAND_A': 1,
                  'FORMULA': 'uint8(255. - A)',
                  'NO_DATA': 0,
                  'RTYPE': 0,
                  'OPTIONS': options,
                  'EXTRA': '--overwrite',
                  'OUTPUT': str(output)}

        # run raster calculation
        processing.run('gdal:rastercalculator', params)

        # remove temp files
        for file in [tmp_slope, tmp_stretch]:
            if file.exists():
                file.unlink()

        return Path(output)

    def shade(self, rgb, shading_file, syntax, crs, output, options, alpha):
        """Create shaded RGB grid from plain color grid and up to two additional shading grids.

        Parameters
        ----------
        rgb : pathlib.Path or str
            file path to RGB raster
        shading_file : pathlib.Path or str
            file path to grey raster for calculation
        syntax : str
            raster calculator syntax
        crs : QgsCoordinateReferenceSystem
            target CRS for output raster
        output : pathlib.Path or str
            file path to shaded raster output
        options : str
            GDAL create options
        alpha : bool
            create RGB or RGBA

        Returns
        -------
        output : pathlib.Path
            file path to shaded raster output

        """
        # create temporary folder
        tmp_folder = Path(QgsProcessingUtils.tempFolder())
        tmp_file = tmp_folder / f'shade.{self.ext}'

        # raster calculator parameters
        params = {'INPUT_A': str(rgb),
                  'BAND_A': 1,
                  'INPUT_B': str(shading_file),
                  'BAND_B': 1,
                  'FORMULA': syntax,
                  'NO_DATA': 0,
                  'RTYPE': 0,
                  'OPTIONS': options,
                  'EXTRA': '--allBands=A --overwrite',
                  'OUTPUT': str(tmp_file)}

        # run raster calculation
        processing.run('gdal:rastercalculator', params)

        # translate parameters
        extra = ['-r bilinear', '-b 1', '-b 2', '-b 3']
        # add alpha channel if required
        if alpha:
            extra.append('-b mask')
            extra.append('-colorinterp_4 alpha')
        extra = ' '.join(extra)

        params = {'INPUT': str(tmp_file),
                  'TARGET_CRS': crs,
                  'DATA_TYPE': 0,
                  'OPTIONS': options,
                  'EXTRA': extra,  # f'-b 1 -b 2 -b 3 -r bilinear -a_nodata "0 0 0"',
                  'OUTPUT': str(output)}

        # run translate
        processing.run('gdal:translate', params)

        # remove tmp file
        if tmp_file.exists():
            tmp_file.unlink()

        return Path(output)

    def name(self):
        return 'exportshadedbathymetry'

    def icon(self):
        return QIcon(str(self.plugin_dir / 'icons' / 'export_shaded_bathymetry.png'))

    def displayName(self):
        return self.tr('Export Shaded Bathymetry')

    def group(self):
        return self.tr('Bathymetry')

    def groupId(self):
        return 'bathymetry'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        doc = Path(self.plugin_dir) / 'doc' / 'export_shaded_bathymetry.help'
        if not doc.is_file():
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return ExportShadedBathymetry()
