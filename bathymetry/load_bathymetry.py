# -*- coding: utf-8 -*-
import os

from qgis.core import (
    QgsBilinearRasterResampler,
    QgsBrightnessContrastFilter,
    QgsColorRampShader,
    QgsLayerTreeLayer,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterNumber,
    QgsProject,
    QgsRasterLayer,
    QgsRasterShader,
    QgsSingleBandPseudoColorRenderer)

from qgis.PyQt.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon, QColor

from .bathymetry import Bathymetry
from .. import utils

class LoadBathymetry(QgsProcessingAlgorithm, Bathymetry):
    """Load Bathymetry"""
    #processing parameters
    # inputs:
    INPUT = 'INPUT'
    BAND = 'BAND'
    COLORRAMP = 'COLORRAMP'
    MIN = 'MIN'
    MAX = 'MAX'
    Z_POS_DOWN = 'Z_POS_DOWN'
    # process:
    LAYERS = {}
    # outputs:
    GROUP = 'GROUP'
    DEM_LAYER = 'DEM_LAYER'
    HILLSHADE_LAYER = 'HILLSHADE_LAYER'

    def __init__(self):
        """Initialize LoadBathymetry"""
        super(LoadBathymetry, self).__init__()
        
        # available color_ramps
        self.color_ramps = {
            'Haxby'   : ['#2539af','#287ffb','#32beff','#6aebff','#8aecae','#cdffa2','#f0ec79','#ffbd57','#ffa144','#ffba85','#ffffff'],
            'Blues'   : ['#08306b','#08519c','#1c6cb1','#3585c0','#529dcc','#73b3d8','#9ac8e1','#bad6eb','#d1e3f3','#e4eff9','#f7fbff'],
            'Rainbow' : ['#640065','#7b0090','#8200b8','#7c00de','#6500ff','#3700ff','#0009ff','#004aff','#007eff','#00acff','#00d8ff','#00fff8','#00ff8a','#05ff00','#38ff00','#5fff00','#83ff00','#a4ff00','#c4ff00','#e3ff00','#fffd00','#ffdd00','#ffbc00','#ff9900','#ff7400','#ff4c00','#ff1e00','#ff0000','#ff0000','#ff0000','#ff0000','#ff0000','#ff0000','#ec0000','#da0000','#c70000','#b40000','#a00000','#8c0000','#770000','#610000']
        }
        
        # list of all color_ramps
        self.colors_list = []
        for key in self.color_ramps.keys():
            self.colors_list.append(key)
        
        # style files for layers
        self.style_hillshade_prj = ':/plugins/cruisetools/styles/style_hillshade_prj.qml'
        self.style_hillshade_geo = ':/plugins/cruisetools/styles/style_hillshade_geo.qml'
        self.style_hillshade_pos_down_prj = ':/plugins/cruisetools/styles/style_hillshade_pos_down_prj.qml'
        self.style_hillshade_pos_down_geo = ':/plugins/cruisetools/styles/style_hillshade_pos_down_geo.qml'
        
        # initialize default configuration
        self.initConfig()

    def initConfig(self):
        """Get default values from CruiseToolsConfig"""
        self.min, self.max = self.config.get_minmax()
        self.color_ramp_default = self.config.getint(self.module, 'color_ramp')

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFile(
                name=self.INPUT,
                description=self.tr('Input Raster File'),
                behavior=QgsProcessingParameterFile.File,
                optional=False,
                fileFilter='GTiff (*.tif *.tiff);;netCDF (*.nc *.grd)')
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.COLORRAMP,
                description=self.tr('Colorramp'),
                options=self.colors_list,
                defaultValue=self.color_ramp_default,
                optional=False,
                allowMultiple=False)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.MAX,
                description=self.tr('Maximum Depth'),
                type=QgsProcessingParameterNumber.Integer,
                optional=False,
                defaultValue=self.max)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.MIN,
                description=self.tr('Minimum Depth'),
                type=QgsProcessingParameterNumber.Integer,
                optional=False,
                defaultValue=self.min)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.Z_POS_DOWN,
                description=self.tr('Raster Z positive down'),
                optional=False,
                defaultValue=False)
        )

    def processAlgorithm(self, parameters, context, feedback):
        # get input variables
        raster = self.parameterAsFile(parameters, self.INPUT, context)
        color_ramp = self.parameterAsEnum(parameters, self.COLORRAMP, context)
        colors = self.color_ramps[self.colors_list[color_ramp]]
        min = self.parameterAsInt(parameters, self.MIN, context)
        max = self.parameterAsInt(parameters, self.MAX, context)
        z_pos_down = self.parameterAsBoolean(parameters, self.Z_POS_DOWN, context)
        
        # set new default values in config
        feedback.pushConsoleInfo(self.tr(f'Storing new default settings in config...'))
        self.config.set(self.module, 'min', min)
        self.config.set(self.module, 'max', max)
        self.config.set(self.module, 'color_ramp', color_ramp)
        
        # get file info
        base_path, base_name, ext = utils.get_info_from_path(raster)
        
        # BATHY:
        # load grid
        feedback.pushConsoleInfo(self.tr(f'Creating new raster layer [ {base_name} ]...'))
        dem_layer = QgsRasterLayer(raster, base_name)
        
        # test if the files loads properly
        if not dem_layer.isValid():
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        
        # create color scale values
        feedback.pushConsoleInfo(self.tr(f'Creating color ramp...'))
        n_values = len(colors)
        width = max - min
        step = width / (n_values - 1)
        values = []
        value = min
        for i in range(n_values):
            values.append(value)
            value = value + step
        
        # create color_ramp
        ramp = []
        for i, item in enumerate(colors):
            ramp.append(QgsColorRampShader.ColorRampItem(values[i], QColor(str(item)), str(values[i])))
        color_ramp = QgsColorRampShader()
        color_ramp.setColorRampItemList(ramp)
        color_ramp.setColorRampType(QgsColorRampShader.Interpolated)
        
        # create shader and set color_ramp
        feedback.pushConsoleInfo(self.tr(f'Creating raster shader...'))
        shader = QgsRasterShader()
        shader.setRasterShaderFunction(color_ramp)
        
        # create renderer
        feedback.pushConsoleInfo(self.tr(f'Creating raster renderer...'))
        renderer = QgsSingleBandPseudoColorRenderer(dem_layer.dataProvider(), dem_layer.type(), shader)
        
        # set min max values
        renderer.setClassificationMin(min)
        renderer.setClassificationMax(max)
        
        # apply renderer to layer
        dem_layer.setRenderer(renderer)
        
        # apply brightness & contrast of layer
        feedback.pushConsoleInfo(self.tr(f'Adjusting display filters...'))
        brightness_filter = QgsBrightnessContrastFilter()
        brightness_filter.setBrightness(-20)
        brightness_filter.setContrast(10)
        dem_layer.pipe().set(brightness_filter)
        
        # apply resample filter (Bilinear)
        feedback.pushConsoleInfo(self.tr(f'Setting up resampling...'))
        resample_filter = dem_layer.resampleFilter()
        resample_filter.setZoomedInResampler(QgsBilinearRasterResampler())
        resample_filter.setZoomedOutResampler(QgsBilinearRasterResampler())
        
        # trigger repaint
        dem_layer.triggerRepaint()
        
        # 50% done
        if feedback.isCanceled():
            return {}
        feedback.setProgress(50)
        
        # HILLSHADE:
        # load grid again with layer style file style_hillshade.qml
        feedback.pushConsoleInfo(self.tr(f'Creating new hillshade layer [ {base_name}_hillshade ]...'))
        hillshade_layer = QgsRasterLayer(raster, base_name + '_hillshade')
        
        # if raster is geographic, load hillshade_geo style (different exaggeration)
        # if raster is Z positive down, load *_pos_down_* style
        feedback.pushConsoleInfo(self.tr(f'Setting hillshade style...\n'))
        if dem_layer.crs().isGeographic() and not z_pos_down:
            hillshade_layer.loadNamedStyle(self.style_hillshade_geo)
        elif dem_layer.crs().isGeographic() and z_pos_down:
            hillshade_layer.loadNamedStyle(self.style_hillshade_pos_down_geo)
        # else load hillste_prj style
        elif z_pos_down:
            hillshade_layer.loadNamedStyle(self.style_hillshade_pos_down_prj)
        else:
            hillshade_layer.loadNamedStyle(self.style_hillshade_prj)
        
        # trigger repaint
        hillshade_layer.triggerRepaint()
        
        # pack layers and base name for postProcessAlgorithm()
        self.LAYERS['base_name'] = base_name
        self.LAYERS['dem_layer'] = dem_layer
        self.LAYERS['hillshade_layer'] = hillshade_layer
        
        # 100% done
        if feedback.isCanceled():
            return {}
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Grid loaded successfully!\n'))
        
        return {}

    def postProcessAlgorithm(self, context, feedback):
        project = context.project()
        
        # create group
        root = project.instance().layerTreeRoot()
        group = root.addGroup(self.LAYERS['base_name'])
        
        # load dem layer
        dem_layer = self.LAYERS['dem_layer']
        project.addMapLayer(dem_layer, False)
        group.insertLayer(1, dem_layer)
        
        # load hillshade layer
        hillshade_layer = self.LAYERS['hillshade_layer']
        project.addMapLayer(hillshade_layer, False)
        group.insertLayer(0, hillshade_layer)
        
        result = {self.GROUP : group,
                  self.DEM_LAYER : dem_layer,
                  self.HILLSHADE_LAYER : hillshade_layer}
        
        return result

    def name(self):
        return 'loadbathymetry'

    def icon(self):
        icon = QIcon(f'{self.plugin_dir}/icons/load_bathymetry.png')
        return icon

    def displayName(self):
        return self.tr('Load Bathymetry')

    def group(self):
        return self.tr('Bathymetry')

    def groupId(self):
        return 'bathymetry'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        doc = f'{self.plugin_dir}/doc/load_bathymetry.help'
        if not os.path.exists(doc):
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return LoadBathymetry()
