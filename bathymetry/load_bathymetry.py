import os

from qgis.core import (
    QgsBilinearRasterResampler,
    QgsBrightnessContrastFilter,
    QgsColorRampShader,
    # QgsLayerTreeLayer,
    # QgsProcessing,
    QgsProcessingAlgorithm,
    # QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterLayer,
    QgsProject,
    QgsMapLayer,
    QgsRasterLayer,
    QgsRasterShader,
    QgsSingleBandPseudoColorRenderer
)

from qgis.PyQt.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon, QColor

from .bathymetry import Bathymetry
from .. import utils

class LoadBathymetry(QgsProcessingAlgorithm, Bathymetry):
    """Load Bathymetry."""
    
    # Processing parameters
    # inputs:
    INPUT = 'INPUT'
    BAND = 'BAND'
    COLORMAP_MODUS = 'COLORMAP_MODUS'
    COLORRAMP = 'COLORRAMP'
    MIN = 'MIN'
    MAX = 'MAX'
    Z_POS_DOWN = 'Z_POS_DOWN'
    REF_RASTER = 'REF_RASTER'
    # process:
    LAYERS = {}
    # outputs:
    GROUP = 'GROUP'
    DEM_LAYER = 'DEM_LAYER'
    HILLSHADE_LAYER = 'HILLSHADE_LAYER'

    def __init__(self):
        """Initialize LoadBathymetry."""
        super(LoadBathymetry, self).__init__()
        
        # available color_ramps
        self.color_ramps = {
            'Haxby'   : ['#2539af', '#287ffb', '#32beff', '#6aebff', '#8aecae', '#cdffa2', '#f0ec79', '#ffbd57', '#ffa144', '#ffba85', '#ffffff'],
            'Blues'   : ['#08306b', '#08519c', '#1c6cb1', '#3585c0', '#529dcc', '#73b3d8', '#9ac8e1', '#bad6eb', '#d1e3f3', '#e4eff9', '#f7fbff'],
            'Rainbow' : ['#640065', '#7b0090', '#8200b8', '#7c00de', '#6500ff', '#3700ff', '#0009ff', '#004aff', '#007eff', '#00acff', '#00d8ff', '#00fff8', '#00ff8a', '#05ff00', '#38ff00', '#5fff00', '#83ff00', '#a4ff00', '#c4ff00', '#e3ff00', '#fffd00', '#ffdd00', '#ffbc00', '#ff9900', '#ff7400', '#ff4c00', '#ff1e00', '#ff0000', '#ff0000', '#ff0000', '#ff0000', '#ff0000', '#ff0000', '#ec0000', '#da0000', '#c70000', '#b40000', '#a00000', '#8c0000', '#770000', '#610000'],
            'Mako'    : ['#0b0405', '#26172b', '#382a54', '#414082', '#395d9c', '#357ba3', '#3498a9', '#3eb4ad', '#62cfac', '#abe2be', '#def5e5'],
            'Deep'    : ['#281a2c', '#281b2d', '#291c2f', '#2a1c30', '#2b1d32', '#2b1e33', '#2c1f34', '#2d1f36', '#2d2037', '#2e2139', '#2f223a', '#2f223b', '#30233d', '#30243e', '#312540', '#322541', '#322643', '#332744', '#342846', '#342847', '#352949', '#352a4a', '#362a4c', '#362b4d', '#372c4f', '#382d51', '#382d52', '#392e54', '#392f55', '#3a3057', '#3a3058', '#3b315a', '#3b325c', '#3c325d', '#3c335f', '#3d3461', '#3d3562', '#3d3564', '#3e3666', '#3e3767', '#3f3869', '#3f386b', '#3f396c', '#403a6e', '#403b70', '#403c71', '#403c73', '#413d75', '#413e76', '#413f78', '#41407a', '#41407b', '#41417d', '#41427e', '#424380', '#414481', '#414583', '#414684', '#414785', '#414887', '#414988', '#414a89', '#414b8a', '#404c8b', '#404d8c', '#404e8d', '#404f8d', '#3f508e', '#3f528f', '#3f538f', '#3f5490', '#3f5590', '#3e5691', '#3e5791', '#3e5892', '#3e5992', '#3e5a92', '#3e5b93', '#3e5c93', '#3e5e93', '#3e5f93', '#3e6094', '#3e6194', '#3e6294', '#3e6394', '#3e6495', '#3e6595', '#3e6695', '#3e6795', '#3e6896', '#3e6996', '#3e6a96', '#3e6b96', '#3f6c96', '#3f6d97', '#3f6e97', '#3f6f97', '#3f7097', '#407197', '#407298', '#407398', '#407498', '#407598', '#417698', '#417799', '#417899', '#427999', '#427a99', '#427b99', '#427c9a', '#437d9a', '#437e9a', '#437f9a', '#44809b', '#44819b', '#44829b', '#44839b', '#45849b', '#45859c', '#45869c', '#46879c', '#46889c', '#46899d', '#478a9d', '#478b9d', '#478c9d', '#488d9d', '#488e9e', '#488f9e', '#49909e', '#49919e', '#49929f', '#4a939f', '#4a949f', '#4a959f', '#4b96a0', '#4b97a0', '#4b98a0', '#4c99a0', '#4c9aa0', '#4d9ba1', '#4d9ca1', '#4d9da1', '#4e9ea1', '#4e9fa1', '#4fa0a2', '#4fa1a2', '#4fa2a2', '#50a3a2', '#50a4a2', '#51a5a2', '#51a6a2', '#51a7a3', '#52a8a3', '#52a9a3', '#53aaa3', '#53aba3', '#54aca3', '#55ada3', '#55aea3', '#56afa4', '#56b0a4', '#57b1a4', '#58b2a4', '#58b3a4', '#59b4a4', '#5ab6a4', '#5ab7a4', '#5bb8a4', '#5cb9a4', '#5dbaa4', '#5ebba4', '#5fbca4', '#60bda4', '#61bea4', '#62bfa4', '#63c0a4', '#64c1a4', '#65c2a4', '#66c2a4', '#67c3a4', '#69c4a4', '#6ac5a4', '#6bc6a3', '#6dc7a3', '#6ec8a3', '#70c9a3', '#71caa3', '#73cba3', '#75cca3', '#76cda3', '#78cea3', '#7acea3', '#7ccfa3', '#7dd0a3', '#7fd1a3', '#81d2a3', '#83d3a3', '#85d3a3', '#87d4a3', '#89d5a3', '#8bd6a3', '#8dd7a3', '#90d7a4', '#92d8a4', '#94d9a4', '#96daa4', '#98daa4', '#9adba5', '#9cdca5', '#9fdda5', '#a1dda6', '#a3dea6', '#a5dfa7', '#a7e0a7', '#aae0a8', '#ace1a8', '#aee2a9', '#b0e2a9', '#b2e3aa', '#b5e4aa', '#b7e5ab', '#b9e5ac', '#bbe6ac', '#bde7ad', '#bfe7ae', '#c1e8af', '#c4e9af', '#c6eab0', '#c8eab1', '#caebb2', '#ccecb3', '#ceecb3', '#d0edb4', '#d2eeb5', '#d4efb6', '#d7efb7', '#d9f0b8', '#dbf1b9', '#ddf2ba', '#dff2bb', '#e1f3bc', '#e3f4bd', '#e5f4be', '#e7f5bf', '#e9f6c0', '#ebf7c1', '#edf7c3', '#eff8c4', '#f1f9c5', '#f3fac6', '#f5fac7', '#f7fbc8', '#f9fcca', '#fbfdcb', '#fdfecc'],
        }
        
        # list of all color_ramps
        self.colors_list = []
        for key in self.color_ramps.keys():
            self.colors_list.append(key)
            
        # set colormap modi options
        self.colormap_modus_options = ['Manual input', 'Copy style from existing layer']
        
        # style files for layers
        self.style_hillshade_prj = ':/plugins/cruisetools/styles/style_hillshade_prj.qml'
        self.style_hillshade_geo = ':/plugins/cruisetools/styles/style_hillshade_geo.qml'
        self.style_hillshade_pos_down_prj = ':/plugins/cruisetools/styles/style_hillshade_pos_down_prj.qml'
        self.style_hillshade_pos_down_geo = ':/plugins/cruisetools/styles/style_hillshade_pos_down_geo.qml'
        
        # initialize default configuration
        self.initConfig()

    def initConfig(self):
        """Get default values from CruiseToolsConfig."""
        self.min, self.max = self.config.get_minmax()
        self.color_ramp_default = self.config.getint(self.module, 'color_ramp')
        self.colormap_modus_default = self.config.getint(self.module, 'colormap_modus')
        self.raster_layer_default = self.config.get(self.module, 'raster_layer')

    def initAlgorithm(self, config=None):  # noqa
        self.addParameter(
            QgsProcessingParameterFile(
                name=self.INPUT,
                description=self.tr('Input Raster File'),
                behavior=QgsProcessingParameterFile.File,
                optional=False,
                fileFilter='GTiff (*.tif *.tiff);;netCDF (*.nc *.grd)')
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
                name=self.COLORMAP_MODUS,
                description=self.tr('Use colormap from'),
                options=list(self.colormap_modus_options),
                defaultValue=self.colormap_modus_default,
                optional=False,
                allowMultiple=False)
        )
        self.parameterDefinition(self.COLORMAP_MODUS).setMetadata({
            'widget_wrapper': {
                'useCheckBoxes': True,
                'columns': 2,
            }
        })
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
        raster_layers = [lyr for lyr in QgsProject.instance().mapLayers().values() if lyr.type() == QgsMapLayer.RasterLayer]
        raster_layer_names = [r.name() for r in raster_layers]
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                name=self.REF_RASTER,
                description=self.tr('Reference Raster Style'),
                defaultValue=(
                    self.raster_layer_default
                    if self.raster_layer_default in raster_layer_names
                    else None
                ),  # None
                optional=True)
        )

    def processAlgorithm(self, parameters, context, feedback):  # noqa
        # get input variables
        raster = self.parameterAsFile(parameters, self.INPUT, context)
        colormap_modus = self.parameterAsEnum(parameters, self.COLORMAP_MODUS, context)
        color_ramp = self.parameterAsEnum(parameters, self.COLORRAMP, context)
        colors = self.color_ramps[self.colors_list[color_ramp]]
        cmin = self.parameterAsInt(parameters, self.MIN, context)
        cmax = self.parameterAsInt(parameters, self.MAX, context)
        z_pos_down = self.parameterAsBoolean(parameters, self.Z_POS_DOWN, context)
        raster_layer = self.parameterAsRasterLayer(parameters, self.REF_RASTER, context)
        
        # set new default values in config
        feedback.pushConsoleInfo(self.tr('Storing new default settings in config...'))
        self.config.set(self.module, 'colormap_modus', colormap_modus)
        self.config.set(self.module, 'min', cmin)
        self.config.set(self.module, 'max', cmax)
        self.config.set(self.module, 'color_ramp', color_ramp)
        if raster_layer is not None:
            self.config.set(self.module, 'raster_layer', raster_layer.name())
        
        # get file info
        base_path, base_name, ext = utils.get_info_from_path(raster)
        
        # BATHY:
        # load grid
        feedback.pushConsoleInfo(self.tr(f'Creating new raster layer [ {base_name} ]...'))
        dem_layer = QgsRasterLayer(raster, base_name)
        
        # test if the files loads properly
        if not dem_layer.isValid():
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))
        
        if colormap_modus == 0:
            # create color scale values
            feedback.pushConsoleInfo(self.tr('Creating color ramp...'))
            n_values = len(colors)
            width = cmax - cmin
            step = width / (n_values - 1)
            values = []
            value = cmin
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
            feedback.pushConsoleInfo(self.tr('Creating raster shader...'))
            shader = QgsRasterShader()
            shader.setRasterShaderFunction(color_ramp)
            
            # create renderer
            feedback.pushConsoleInfo(self.tr('Creating raster renderer...'))
            renderer = QgsSingleBandPseudoColorRenderer(dem_layer.dataProvider(), dem_layer.type(), shader)
            
            # set min max values
            renderer.setClassificationMin(cmin)
            renderer.setClassificationMax(cmax)
            
            # apply renderer to layer
            dem_layer.setRenderer(renderer)
            
            # apply brightness & contrast of layer
            feedback.pushConsoleInfo(self.tr('Adjusting display filters...'))
            brightness_filter = QgsBrightnessContrastFilter()
            brightness_filter.setBrightness(-20)
            brightness_filter.setContrast(10)
            dem_layer.pipe().set(brightness_filter)
            
            # apply resample filter (Bilinear)
            feedback.pushConsoleInfo(self.tr('Setting up resampling...'))
            resample_filter = dem_layer.resampleFilter()
            resample_filter.setZoomedInResampler(QgsBilinearRasterResampler())
            resample_filter.setZoomedOutResampler(QgsBilinearRasterResampler())
            
        elif colormap_modus == 1:
            # get the name of the reference layer's current style
            style_name = raster_layer.styleManager().currentStyle()

            # get style from existing raster layer
            style = raster_layer.styleManager().style(style_name)
            
            # add the style to the target layer with a custom name (in this case: 'copied')
            style_name_dst = 'copied'
            dem_layer.styleManager().addStyle(style_name_dst, style)
            
            # set the added style as the current style
            dem_layer.styleManager().setCurrentStyle(style_name_dst)

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
        feedback.pushConsoleInfo(self.tr('Setting hillshade style...\n'))
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

    def postProcessAlgorithm(self, context, feedback):  # noqa
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

    def name(self):  # noqa
        return 'loadbathymetry'

    def icon(self):  # noqa
        icon = QIcon(f'{self.plugin_dir}/icons/load_bathymetry.png')
        return icon

    def displayName(self):  # noqa
        return self.tr('Load Bathymetry')

    def group(self):  # noqa
        return self.tr('Bathymetry')

    def groupId(self):  # noqa
        return 'bathymetry'

    def tr(self, string):  # noqa
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):  # noqa
        doc = f'{self.plugin_dir}/doc/load_bathymetry.help'
        if not os.path.exists(doc):
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):  # noqa
        return LoadBathymetry()
