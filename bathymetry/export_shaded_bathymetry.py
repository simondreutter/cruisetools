# -*- coding: utf-8 -*-
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

class ExportShadedBathymetry(QgsProcessingAlgorithm,Bathymetry):
    '''Export Shaded Bathymetry'''
    #processing parameters
    # inputs:
    INPUT = 'INPUT'
    OPTIONS = 'OPTIONS'
    SHADE_BY = 'SHADE_BY'
    Z_POS_DOWN = 'Z_POS_DOWN'
    # outputs:
    OUTPUT = 'OUTPUT'

    def __init__(self):
        '''Initialize ExportShadedBathymetry'''
        super(ExportShadedBathymetry, self).__init__()
        
        # available shading methods
        self.shaders = [self.tr('Hillshade'),
                        self.tr('Slope'),
                        self.tr('Hillshade AND Slope')]
        
        # default extension for temporary files
        self.ext = 'tif'
        
        self.azimuth = 315.0
        self.altitude = 45.0
        
        # set default vertical exaggeration
        self.hs_z_factor = 5.0
        self.slope_z_factor = 3.0
        
        # initialize default configuration
        self.initConfig()

    def initConfig(self):
        '''Get default values from CruiseToolsConfig'''
        self.shader = self.config.get(self.module,'shader')

    def initAlgorithm(self, config=None):
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
                name=self.SHADE_BY,
                description=self.tr('Shade By'),
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

    def processAlgorithm(self, parameters, context, feedback):
        # get input variables
        raster_layer = self.parameterAsRasterLayer(parameters,self.INPUT,context)
        shade_by = self.parameterAsEnum(parameters,self.SHADE_BY,context)
        options = self.parameterAsString(parameters,self.OPTIONS,context)
        output = self.parameterAsOutputLayer(parameters,self.OUTPUT,context)
        z_pos_down = self.parameterAsBoolean(parameters,self.Z_POS_DOWN,context)
        
        feedback.pushConsoleInfo(self.tr(f'Shading by {self.shaders[shade_by]}\n'))
        
        # set new default values in config
        feedback.pushConsoleInfo(self.tr(f'Storing new default settings in config...'))
        self.config.set(self.module,'shader',shade_by)
        
        # create empty temp file variables
        rgb_file,hs_file,slope_file,slope_stretch_file,slope_inv_file = None,None,None,None,None
        
        # create switches for shade_by
        hillshade,slope,combo = False,False,False
        
        # set settings by shade_by
        if shade_by == 0:
            hillshade = True
            syntax = 'uint8(((A/255.)*(((B*0.5)+(255.*0.5))/255.))*255)'
        elif shade_by == 1:
            slope = True
            syntax = 'uint8(((A/255.)*(((C*0.5)+(255.*0.5))/255.))*255)'
        elif shade_by == 2:
            combo = True
            syntax = 'uint8(((A/255.)*(((B*0.3)+(255.*0.7))/255.)*(((C*0.3)+(255.*0.7))/255.))*255)'
        
        # create temporary folder
        tmp_folder = QgsProcessingUtils.tempFolder()
        
        # render selected layer with defined symbology as rgb raster
        feedback.pushConsoleInfo(self.tr(f'Rendering layer to RGB...'))
        rgb_file = os.path.join(tmp_folder,f'rgb.{self.ext}')
        error, result = self.create_rgb(raster_layer,rgb_file)
        if error:
            feedback.reportError(self.tr(result),fatalError=True)
            return {}
        
        # 20% done
        feedback.setProgress(20)
        
        # get crs from layer
        crs_raster = raster_layer.crs()
        
        # get scale for vertical units
        scale = self.get_scale(crs_raster)
        
        if hillshade or combo:
            # create hillshade
            feedback.pushConsoleInfo(self.tr(f'Creating hillshade grid...'))
            # if raster is z positive down flip illumination direction
            if z_pos_down:
                self.azimuth = (self.azimuth - 180.) % 360.
            hs_file = os.path.join(tmp_folder,f'hs.{self.ext}')
            self.create_hs(raster_layer,self.hs_z_factor,scale,self.azimuth,self.altitude,hs_file,options)
        
        # 40% done
        feedback.setProgress(40)
        
        if slope or combo:
            # create slope
            feedback.pushConsoleInfo(self.tr(f'Creating slope grid...'))
            slope_file = os.path.join(tmp_folder,f'slope.{self.ext}')
            self.create_slope(raster_layer,self.slope_z_factor,scale,slope_file,options)
            
            # 60% done
            feedback.setProgress(60)
            
            # stretch slope to min max
            feedback.pushConsoleInfo(self.tr(f'Stretching slope grid...'))
            slope_stretch_file = os.path.join(tmp_folder,f'slope_stretch.{self.ext}')
            self.stretch_min_max(slope_file,slope_stretch_file,options)
            
            # 70% done
            feedback.setProgress(70)
            
            # invert slope (White to Black instead of Black to White)
            feedback.pushConsoleInfo(self.tr(f'Inverting stretched slope grid...'))
            slope_inv_file = os.path.join(tmp_folder,f'slope_inv.{self.ext}')
            self.invert(slope_stretch_file,slope_inv_file,options)
        
        # 80% done
        feedback.setProgress(80)
        
        # shading computation
        feedback.pushConsoleInfo(self.tr(f'Calculating output raster...\n'))
        self.shade(rgb_file,hs_file,slope_inv_file,syntax,output,crs_raster,options)
        
        # 99% done
        feedback.setProgress(99)
        
        # delete temp files
        for file in [rgb_file,hs_file,slope_file,slope_stretch_file,slope_inv_file]:
            if os.path.isfile(str(file)):
                os.remove(file)
        
        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Shaded bathymetry file is created!\n'))
        
        result = {self.OUTPUT : output}
        
        return result

    def create_rgb(self,raster_layer,output):
        '''Render and write RGB file

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
    
        '''
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
        error = fwriter.writeRaster(pipe,width,height,extent,crs_raster)
        if error != fwriter.NoError:
            return 1, 'RGB file could not be rendered!'
        
        return 0, output

    def get_scale(self,crs):
        '''Get scale for vertical units in grid

        Parameters
        ----------
        crs : QgsCoordinateReferenceSystem
            input CRS

        Returns
        -------
        scale : float
            vertical scale

        '''
        # if the grid is geographic, vertical will be interpreted as degree
        # hence the scale needs to be 0.000009.
        if crs.isGeographic():
            scale = 0.000009
        # otherwise it's considered in meters and the scale is 1.
        else:
            scale = 1.0
        
        return scale

    def create_hs(self,input,z_factor,scale,azimuth,altitude,output,options):
        '''Create hillshade grid from raster input

        Parameters
        ----------
        input : str
            file path to raster DEM
        z_factor : float
            vertical exaggeration
        scale : float
            1.0 for meters and 0.000009 for geographic raster
        azimuth : float
            direction angle of illumination
        altitude : float
            altitude angle of illumination
        output : str
            file path to hillshade raster output
        options : str
            GDAL create options

        Returns
        -------
        output : str
            file path to hillshade raster output

        '''
        # hillshade parameters
        hs_params = {'INPUT': input,
                    'BAND': 1,
                    'Z_FACTOR': z_factor*scale,
                    'SCALE': 1.0,
                    'AZIMUTH': azimuth,
                    'ALTITUDE': altitude,
                    'COMPUTE_EDGES': True,
                    'MULTIDIRECTIONAL': False,
                    'OPTIONS': options,
                    'OUTPUT': output}
        
        # run hillshade
        processing.run('gdal:hillshade', hs_params)
        
        return output

    def create_slope(self,input,z_factor,scale,output,options):
        '''Create slope grid from raster input

        Parameters
        ----------
        input : str
            file path to raster DEM
        z_factor : float
            vertical exaggeration
        scale : float
            1.0 for meters and 0.000009 for geographic raster
        output : str
            file path to slope raster output
        options : str
            GDAL create options

        Returns
        -------
        output : str
            file path to slope raster output

        '''
        # slope parameters
        slope_params = {'INPUT': input,
                        'Z_FACTOR': z_factor*scale,
                        'OPTIONS': options,
                        'OUTPUT': output}
        
        # run slope
        processing.run('qgis:slope', slope_params)
        
        return output

    def stretch_min_max(self,input,output,options):
        '''Stretch grey scale image to min max

        Parameters
        ----------
        input : str
            file path to raster
        output : str
            file path to raster output
        options : str
            GDAL create options

        Returns
        -------
        output : str
            file path to raster output

        '''
        # min max values (byte)
        dmin = 1.
        dmax = 254.
        
        # create raster layer from input to get stats
        raster_layer = QgsRasterLayer(input, 'tmp', 'gdal')
        extent = raster_layer.extent()
        provider = raster_layer.dataProvider()
        
        # get stats
        stats = provider.bandStatistics(1, QgsRasterBandStats.All, extent, 0)
        smin = stats.minimumValue
        smax = stats.maximumValue
        
        # translate parameters
        translate_params = {'INPUT': input,
                            'NO_DATA': 0,
                            'RTYPE': 0,
                            'OPTIONS': options,
                            'EXTRA': '-scale {} {} {} {} -r bilinear'.format(smin,smax,dmin,dmax),
                            'OUTPUT': output}
        
        # run translate
        processing.run('gdal:translate', translate_params)
        
        # dereference raster layer
        raster_layer = None
        
        return output

    def invert(self,input,output,options):
        '''Create inverted slope grid

        Parameters
        ----------
        input : str
            file path to raster
        output : str
            file path to raster output
        options : str
            GDAL create options

        Returns
        -------
        output : str
            file path to raster output

        '''
        # raster calculator parameters
        calc_params = {'INPUT_A': input,
                        'BAND_A': 1,
                        'FORMULA': 'uint8(255. - A)',
                        'NO_DATA': 0,
                        'RTYPE': 0,
                        'OPTIONS': options,
                        'EXTRA': '--overwrite',
                        'OUTPUT': output}
        
        # run raster calculation
        processing.run('gdal:rastercalculator', calc_params)
        
        return output

    def shade(self,rgb,b,c,syntax,output,crs,options):
        '''Create shaded RGB grid from plain color grid and up to two additional shading grids

        Parameters
        ----------
        rgb : str
            file path to RGB raster
        b : str
            file path to grey raster for calculation
        c : str
            file path to grey raster for calculation
        syntax : str
            raster calculator syntax
        output : str
            file path to shaded raster output
        crs : QgsCoordinateReferenceSystem
            target CRS for output raster
        options : str
            GDAL create options

        Returns
        -------
        output : str
            file path to shaded raster output

        '''
        # create temporary folder
        tmp_folder = QgsProcessingUtils.tempFolder()
        tmp_file = os.path.join(tmp_folder,f'shade.{self.ext}')
        
        # raster calculator parameters
        calc_params = {'INPUT_A': rgb,
                        'BAND_A': 1,
                        'INPUT_B': b,
                        'BAND_B': 1,
                        'INPUT_C': c,
                        'BAND_C': 1,
                        'FORMULA': syntax,
                        'NO_DATA': 0,
                        'RTYPE': 0,
                        'OPTIONS': options,
                        'EXTRA': '--allBands=A --overwrite',
                        'OUTPUT': tmp_file}
        
        # run raster calculation
        processing.run('gdal:rastercalculator', calc_params)
        
        # translate parameters
        translate_params = {'INPUT': tmp_file,
                            'TARGET_CRS' : crs,
                            'NO_DATA': 0,
                            'RTYPE': 0,
                            'OPTIONS': options,
                            'EXTRA': '-b 1 -b 2 -b 3 -r bilinear -a_nodata "0 0 0"',
                            'OUTPUT': output}
        
        # run translate
        processing.run('gdal:translate', translate_params)
        
        # remove tmp file
        if os.path.isfile(tmp_file):
            os.remove(tmp_file)
        
        return output

    def name(self):
        return 'exportshadedbathymetry'

    def icon(self):
        icon = QIcon(f'{self.plugin_dir}/icons/export_shaded_bathymetry.png')
        return icon

    def displayName(self):
        return self.tr('Export Shaded Bathymetry')

    def group(self):
        return self.tr('Bathymetry')

    def groupId(self):
        return 'bathymetry'

    def tr(self, string):
        return QCoreApplication.translate('Processing',string)

    def shortHelpString(self):
        doc = f'{self.plugin_dir}/doc/export_shaded_bathymetry.help'
        if not os.path.exists(doc):
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return ExportShadedBathymetry()
