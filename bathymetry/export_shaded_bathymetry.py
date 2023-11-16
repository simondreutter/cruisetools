import os
import processing

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterEnum,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterString,
    QgsProcessingUtils,
    QgsRasterBandStats,
    QgsRasterFileWriter,
    QgsRasterLayer,
    QgsRasterPipe)

from qgis.PyQt.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon

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

    def initAlgorithm(self, config=None):  # noqa
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                name=self.INPUT,
                description=self.tr('Input Raster Layer'),
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
        
        options_param = QgsProcessingParameterString(name=self.OPTIONS,
                                                     description=self.tr('Additional creation options'),
                                                     defaultValue='',
                                                     optional=True)
        options_param.setFlags(options_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        options_param.setMetadata({
            'widget_wrapper': {
                'class': 'processing.algs.gdal.ui.RasterOptionsWidget.RasterOptionsWidgetWrapper'}})
        self.addParameter(options_param)
        
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                name=self.OUTPUT,
                description=self.tr('Shaded Raster'),
                defaultValue=None,
                optional=False,
                createByDefault=True)
        )

    def processAlgorithm(self, parameters, context, feedback):  # noqa
        # get input variables
        raster_layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        shader = self.parameterAsEnum(parameters, self.SHADER, context)
        options = self.parameterAsString(parameters, self.OPTIONS, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        z_pos_down = self.parameterAsBoolean(parameters, self.Z_POS_DOWN, context)
        
        feedback.pushConsoleInfo(self.tr(f'Shader: {self.shaders[shader]}\n'))
        
        # set new default values in config
        feedback.pushConsoleInfo(self.tr('Storing new default settings in config...'))
        self.config.set(self.module, 'shader', shader)
        
        # create empty temp file variables
        rgb_file, shading_file = None, None
        
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
        tmp_folder = QgsProcessingUtils.tempFolder()
        
        # render selected layer with defined symbology as rgb raster
        feedback.pushConsoleInfo(self.tr('Rendering layer to RGB...'))
        rgb_file = os.path.join(tmp_folder, f'rgb.{self.ext}')
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
        shading_file = os.path.join(tmp_folder, f'shading_file.{self.ext}')
        
        # create shading file
        if hillshade or combo or multi:
            # create hillshade
            feedback.pushConsoleInfo(self.tr('Creating shading grid...'))
            # if raster is z positive down flip illumination direction
            if z_pos_down:
                self.azimuth = (self.azimuth - 180.) % 360.
            shading_file = self.hillshade(raster_layer, self.hillshade_z_factor, scale, self.azimuth, self.altitude, combo, multi, shading_file, options)
        
        elif slope:
            # create slope
            feedback.pushConsoleInfo(self.tr('Creating shading grid...'))
            shading_file = self.slopeshade(raster_layer, self.slope_z_factor, scale, shading_file, options)
        
        # 70% done
        if feedback.isCanceled():
            return {}
        feedback.setProgress(70)
        
        # shading computation
        feedback.pushConsoleInfo(self.tr('Calculating output raster...'))
        syntax = 'uint8(((A/255.)*(((B*0.5)+(255.*0.5))/255.))*255)'
        output = self.shade(rgb_file, shading_file, syntax, crs_raster, output, options)
        
        # 99% done
        if feedback.isCanceled():
            return {}
        feedback.setProgress(99)
        
        # remove temp files
        feedback.pushConsoleInfo(self.tr('Deleting temporary files...\n'))
        for file in [rgb_file, shading_file]:
            if os.path.isfile(str(file)):
                os.remove(file)
        
        # 100% done
        if feedback.isCanceled():
            return {}
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Shaded bathymetry file is created!\n'))
        
        result = {self.OUTPUT : output}
        
        return result

    def create_rgb(self, raster_layer, output):
        """Render and write RGB file.

        Parameters
        ----------
        raster_layer : QgsRasterLayer
            input raster layer with singleband pseudocolor
        output : str
            output file path

        Returns
        -------
        error : boolean
            0/1 - no error/error
        result : str or None
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
        fwriter = QgsRasterFileWriter(output)
        error = fwriter.writeRaster(pipe, width, height, extent, crs_raster)
        if error != fwriter.NoError:
            return 1, 'RGB file could not be rendered!'
        
        return 0, output

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
            scale = 10**7 / 90  # 111111.111...
        # otherwise it's considered in meters and the scale is 1.
        else:
            scale = 1.0
        
        return scale

    def hillshade(self, input, z_factor, scale, azimuth, altitude, combined, multidirectional, output, options):
        """Create hillshade grid from raster input.

        Parameters
        ----------
        input : str
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
        output : str
            file path to hillshade raster output
        options : str
            GDAL create options

        Returns
        -------
        output : str
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
                  'OUTPUT': output}
        
        # run hillshade
        processing.run('gdal:hillshade', params)
        
        return output

    def slopeshade(self, input, z_factor, scale, output, options):
        """Create slope shading grid from raster input.

        Parameters
        ----------
        input : str
            file path to raster DEM
        z_factor : float
            vertical exaggeration
        scale : float
            1.0 for meters and 111111.111 for geographic raster
        output : str
            file path to slope raster output
        options : str
            GDAL create options

        Returns
        -------
        output : str
            file path to slope raster output

        """
        # create temporary folder
        tmp_folder = QgsProcessingUtils.tempFolder()
        tmp_slope = os.path.join(tmp_folder, f'slope.{self.ext}')
        tmp_stretch = os.path.join(tmp_folder, f'stretch.{self.ext}')
        
        # slope parameters
        params = {'INPUT': input,
                  'BAND': 1,
                  'SCALE': scale / z_factor,
                  'COMPUTE_EDGES': True,
                  'OPTIONS': options,
                  'OUTPUT': tmp_slope}
        
        # run slope
        processing.run('gdal:slope', params)
        
        # stretch slope to min-max
        # min max values (byte)
        dmin = 1.
        dmax = 254.
        
        # create raster layer from input to get stats
        raster_layer = QgsRasterLayer(tmp_slope, 'tmp', 'gdal')
        extent = raster_layer.extent()
        provider = raster_layer.dataProvider()
        
        # get stats
        stats = provider.bandStatistics(1, QgsRasterBandStats.All, extent, 0)
        smin = stats.minimumValue
        smax = stats.maximumValue
        
        # translate parameters
        params = {'INPUT': tmp_slope,
                  'NO_DATA': 0,
                  'RTYPE': 0,
                  'OPTIONS': options,
                  'EXTRA': '-scale {} {} {} {} -r bilinear'.format(smin, smax, dmin, dmax),
                  'OUTPUT': tmp_stretch}
        
        # run translate
        processing.run('gdal:translate', params)
        
        # dereference raster layer
        raster_layer = None
        
        # invert slope
        # raster calculator parameters
        params = {'INPUT_A': tmp_stretch,
                  'BAND_A': 1,
                  'FORMULA': 'uint8(255. - A)',
                  'NO_DATA': 0,
                  'RTYPE': 0,
                  'OPTIONS': options,
                  'EXTRA': '--overwrite',
                  'OUTPUT': output}
        
        # run raster calculation
        processing.run('gdal:rastercalculator', params)
        
        # remove temp files
        for file in [tmp_slope, tmp_stretch]:
            if os.path.isfile(str(file)):
                os.remove(file)
        
        return output

    def shade(self, rgb, shading_file, syntax, crs, output, options):
        """Create shaded RGB grid from plain color grid and up to two additional shading grids.

        Parameters
        ----------
        rgb : str
            file path to RGB raster
        shading_file : str
            file path to grey raster for calculation
        syntax : str
            raster calculator syntax
        crs : QgsCoordinateReferenceSystem
            target CRS for output raster
        output : str
            file path to shaded raster output
        options : str
            GDAL create options

        Returns
        -------
        output : str
            file path to shaded raster output

        """
        # create temporary folder
        tmp_folder = QgsProcessingUtils.tempFolder()
        tmp_file = os.path.join(tmp_folder, f'shade.{self.ext}')
        
        # raster calculator parameters
        params = {'INPUT_A': rgb,
                  'BAND_A': 1,
                  'INPUT_B': shading_file,
                  'BAND_B': 1,
                  'FORMULA': syntax,
                  'NO_DATA': 0,
                  'RTYPE': 0,
                  'OPTIONS': options,
                  'EXTRA': '--allBands=A --overwrite',
                  'OUTPUT': tmp_file}
        
        # run raster calculation
        processing.run('gdal:rastercalculator', params)
        
        # translate parameters
        params = {'INPUT': tmp_file,
                  'TARGET_CRS' : crs,
                  'NO_DATA': 0,
                  'DATA_TYPE': 0,
                  'OPTIONS': options,
                  'EXTRA': '-b 1 -b 2 -b 3 -r bilinear -a_nodata "0 0 0"',
                  'OUTPUT': output}
        
        # run translate
        processing.run('gdal:translate', params)
        
        # remove tmp file
        if os.path.isfile(tmp_file):
            os.remove(tmp_file)
        
        return output

    def name(self):  # noqa
        return 'exportshadedbathymetry'

    def icon(self):  # noqa
        icon = QIcon(f'{self.plugin_dir}/icons/export_shaded_bathymetry.png')
        return icon

    def displayName(self):  # noqa
        return self.tr('Export Shaded Bathymetry')

    def group(self):  # noqa
        return self.tr('Bathymetry')

    def groupId(self):  # noqa
        return 'bathymetry'

    def tr(self, string):  # noqa
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):  # noqa
        doc = f'{self.plugin_dir}/doc/export_shaded_bathymetry.help'
        if not os.path.exists(doc):
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):  # noqa
        return ExportShadedBathymetry()
