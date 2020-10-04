# -*- coding: utf-8 -*-
'''
/***************************************************************************
 CruiseTools
                                 A QGIS plugin
 The toolbox you need for marine research cruises (planning and stuff)!
                              -------------------
        begin                : 2019-06-12
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Simon Dreutter & Fynn Warnke
        email                : simon.dreutter@awi.de
                               fynn.warnke@awi.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
'''
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the DockWidget
import os.path

# Import some tools
from qgis.core import *
from qgis.gui import *
from qgis.utils import *
import math, processing
import configparser

# Import Cruise Tools modules
from .utils import *
from .bathymetry import *
from .contours import *
from .vector import *
from .planning import *
from .config import *

# Import GUI
from .ui.ReadmeWindow import ReadmeWindow
from .ui.RasterCoverage import RasterCoverage
from .ui.MBEScoverage import MBEScoverage
from .ui.SettingsWindow_dialog import SettingsWindowDialog

class CruiseTools:
    '''QGIS Plugin Implementation.'''
    def __init__(self, iface):
        '''Constructor.
        
        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        '''
        # Save reference to the QGIS interface
        self.iface = iface
        
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            f'CruiseTools_{locale}.qm')
        
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            
            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
        
        # Declare instance attributes
        self.actions = []
        self.menu = self.tr('&Cruise Tools')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar('CruiseTools')
        self.toolbar.setObjectName('CruiseTools')
        
        #print "** INITIALIZING CruiseTools"
        
        #self.pluginIsActive = False
        self.dockwidget = None
        
        # plugin variables to store some user defaults at runtime
        self.mbes_coverage_raster = None
        
        init_settings()
    
    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        '''Get the translation for a string using Qt translation API.
        
        We implement this ourselves since we do not inherit QObject.
        
        :param message: String for translation.
        :type message: str, QString
        
        :returns: Translated version of message.
        :rtype: QString
        '''
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('CruiseTools', message)
    
    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        '''Add a toolbar icon to the toolbar.
        
        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str
        
        :param text: Text that should be shown in menu items for this action.
        :type text: str
        
        :param callback: Function to be called when the action is triggered.
        :type callback: function
        
        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool
        
        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool
        
        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool
        
        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str
        
        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget
        
        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.
        
        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        '''
        
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        
        if status_tip is not None:
            action.setStatusTip(status_tip)
        
        if whats_this is not None:
            action.setWhatsThis(whats_this)
        
        if add_to_toolbar:
            self.toolbar.addAction(action)
        
        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)
        
        self.actions.append(action)
        
        return action
    
    def initGui(self):
        '''Create the menu entries and toolbar icons inside the QGIS GUI.'''
        # get first start indication
        self.first_start = True 
        
        icon_path = ':/plugins/cruisetools/icons'
        
        # README BUTTON
        icon = QIcon(f'{icon_path}/icon.png')
        readme = self.add_action(icon,
                                    text=self.tr('Cruise Tools'),
                                    callback=self.run_readme,
                                    parent=self.iface.mainWindow())
        readme.setToolTip('Show Cruise Tools README for information and instructions.')
        
        
        # BATHYMETRY SUBMENU
        bathy_menu = QMenu()
        # show tool tips
        bathy_menu.setToolTipsVisible(True)
        
        # load bathymetry button
        icon = QIcon(f'{icon_path}/load_bathy.png')
        load_bathy = bathy_menu.addAction(icon,self.tr('Load Bathymetry'), self.run_load_bathy)
        load_bathy.setToolTip('Load a bathymetry grid file (*.tif, *.nc) with pre defined style and hillshade.\n'
                              'Change color ramp and depth scale in the Cruise Tools settings, or later in the\n'
                              'layer symbology')
        
        # export bathymetry submenu
        icon = QIcon(f'{icon_path}/export_bathy.png')
        export_bathy_submenu = bathy_menu.addMenu(icon,self.tr('Export Shaded Bathymetry'))
        # show tool tips
        export_bathy_submenu.setToolTipsVisible(True)
        
        # export bathymetry buttons
        icon = QIcon(f'{icon_path}/export_combo.png')
        export_bathy_combo = export_bathy_submenu.addAction(icon,self.tr('Slope + Hillshade'), self.run_export_combo)
        export_bathy_combo.setToolTip('Export an RGB version of the selected grid with set color ramp\n'
                                      'and shaded with a combination of slope and hillshade.')
        #
        icon = QIcon(f'{icon_path}/export_hs.png')
        export_bathy_hs = export_bathy_submenu.addAction(icon,self.tr('Hillshade'), self.run_export_hs)
        export_bathy_hs.setToolTip('Export an RGB version of the selected grid with set color ramp\n'
                                   'and shaded by hillshade / synthetic illumination.')
        #
        icon = QIcon(f'{icon_path}/export_slope.png')
        export_bathy_slope = export_bathy_submenu.addAction(icon,self.tr('Slope'), self.run_export_slope)
        export_bathy_slope.setToolTip('Export an RGB version of the selected grid with set color ramp\n'
                                      'and shaded by slope inclination.')
        
        bathy_menu.addSeparator()
        
        # raster coverage button
        icon = QIcon(f'{icon_path}/raster_coverage.png')
        calculate_raster_coverage = bathy_menu.addAction(icon,self.tr('Calculate Raster Coverage'), self.run_calculate_raster_coverage)
        calculate_raster_coverage.setToolTip('Calculate approximate coverage area of raster datasets.')
        
        # setup bathymetry menu
        icon = QIcon(f'{icon_path}/bathy_menu.png')
        self.bathyAction = QAction(icon, 'Bathymetry', self.iface.mainWindow())
        self.bathyAction.setMenu(bathy_menu)
        
        self.bathyButton = QToolButton()
        self.bathyButton.setMenu(bathy_menu)
        self.bathyButton.setDefaultAction(self.bathyAction)
        self.bathyButton.setPopupMode(QToolButton.InstantPopup)
        self.tranformToolbar = self.toolbar.addWidget(self.bathyButton)
        
        
        # CONTOURS SUBMENU
        contour_menu = QMenu()
        # show tool tips
        contour_menu.setToolTipsVisible(True)
        
        # 1000 m contour button
        icon = QIcon(f'{icon_path}/create_contours_1000.png')
        create_contours_1000m = contour_menu.addAction(icon,self.tr('1000 m'), self.run_create_contours_1000)
        create_contours_1000m.setToolTip('Create contour lines with 1000 m interval.')
        # 500 m contour button
        icon = QIcon(f'{icon_path}/create_contours_500.png')
        create_contours_500m = contour_menu.addAction(icon,self.tr('500 m'), self.run_create_contours_500)
        create_contours_500m.setToolTip('Create contour lines with 500 m interval.')
        # 100 m contour button
        icon = QIcon(f'{icon_path}/create_contours_100.png')
        create_contours_100m = contour_menu.addAction(icon,self.tr('100 m'), self.run_create_contours_100)
        create_contours_100m.setToolTip('Create contour lines with 100 m interval.')
        # 50 m contour button
        icon = QIcon(f'{icon_path}/create_contours_50.png')
        create_contours_50m = contour_menu.addAction(icon,self.tr('50 m'), self.run_create_contours_50)
        create_contours_50m.setToolTip('Create contour lines with 50 m interval.')
        # 10 m contour button
        icon = QIcon(f'{icon_path}/create_contours_10.png')
        create_contours_10m = contour_menu.addAction(icon,self.tr('10 m'), self.run_create_contours_10)
        create_contours_10m.setToolTip('Create contour lines with 10 m interval.')
        # 5 m contour button
        icon = QIcon(f'{icon_path}/create_contours_5.png')
        create_contours_5m = contour_menu.addAction(icon,self.tr('5 m'), self.run_create_contours_5)
        create_contours_5m.setToolTip('Create contour lines with 5 m interval.')
        # 1 m contour button
        icon = QIcon(f'{icon_path}/create_contours_1.png')
        create_contours_1m = contour_menu.addAction(icon,self.tr('1 m'), self.run_create_contours_1)
        create_contours_1m.setToolTip('Create contour lines with 1 m interval.')
        
        # setup contour menu
        icon = QIcon(f'{icon_path}/contours_menu.png')
        self.contourAction = QAction(icon, 'Create Contours', self.iface.mainWindow())
        self.contourAction.setMenu(contour_menu)
        
        self.contourButton = QToolButton()
        self.contourButton.setMenu(contour_menu)
        self.contourButton.setDefaultAction(self.contourAction)
        self.contourButton.setPopupMode(QToolButton.InstantPopup)
        self.tranformToolbar = self.toolbar.addWidget(self.contourButton)
        
        # VECTOR SUBMENU
        vector_menu = QMenu()
        # show tool tips
        vector_menu.setToolTipsVisible(True)
        
        # write point coordinates button
        icon = QIcon(f'{icon_path}/write_point_coordinates.png')
        write_point_coordinates = vector_menu.addAction(icon,self.tr('Write Point Coordinates'), self.run_write_point_coordinates)
        write_point_coordinates.setToolTip('Add attributes to the selected point layer containing\n'
                                           'Latitude and Longitude in DD and DDM (EPSG:WGS84).')
        
        # write line length button
        icon = QIcon(f'{icon_path}/write_line_length.png')
        write_line_length = vector_menu.addAction(icon,self.tr('Write Line Length'), self.run_write_line_length)
        write_line_length.setToolTip(f'Add attributes to the selected line layer containing\n'
                                     f'length in meters and nautical miles\n\n'
                                     f'Measurements are ellipsoidal, based on ellispoid\n'
                                     f'({QgsProject.instance().crs().ellipsoidAcronym()}).')
        
        # write polygon area button
        icon = QIcon(f'{icon_path}/write_polygon_area.png')
        write_polygon_area = vector_menu.addAction(icon,self.tr('Write Polygon Area'), self.run_write_polygon_area)
        write_polygon_area.setToolTip(f'Add attributes to the selected polygon layer containing\n'
                                      f'area in square meters and square kilometers.\n\n'
                                      f'Measurements are ellipsoidal, based on ellispoid\n'
                                      f'({QgsProject.instance().crs().ellipsoidAcronym()}).')
        
        # swap vectors button
        icon = QIcon(f'{icon_path}/swap_vectors.png')
        swap_vectors = vector_menu.addAction(icon,self.tr('Swap Vectors'), self.run_swap_vectors)     
        swap_vectors.setToolTip('Swap direction of selected line layer (for contour labels, etc.).')
        
        # setup vector menu
        icon = QIcon(f'{icon_path}/vector_menu.png')
        self.vectorAction = QAction(icon, 'Vector', self.iface.mainWindow())
        self.vectorAction.setMenu(vector_menu)
        
        self.vectorButton = QToolButton()
        self.vectorButton.setMenu(vector_menu)
        self.vectorButton.setDefaultAction(self.vectorAction)
        self.vectorButton.setPopupMode(QToolButton.InstantPopup)
        self.tranformToolbar = self.toolbar.addWidget(self.vectorButton)
        
        # PLANNING SUBMENU
        planning_menu = QMenu()
        # show tool tips
        planning_menu.setToolTipsVisible(True)
        
        # create point planning file button
        icon = QIcon(f'{icon_path}/create_point_planning.png')
        create_point_planning_file = planning_menu.addAction(icon,self.tr('Create Point Planning File'), self.run_create_point_planning_file)
        create_point_planning_file.setToolTip('Create new point layer file (GPKG) for point/station planning purposes.')
        
        # create line planning file button
        icon = QIcon(f'{icon_path}/create_line_planning.png')
        create_line_planning_file = planning_menu.addAction(icon,self.tr('Create Line Planning File'), self.run_create_line_planning_file)
        create_line_planning_file.setToolTip('Create new line layer file (GPKG) for line planning purposes.')
        
        # planning lines to vertices button
        icon = QIcon(f'{icon_path}/create_line_vertices.png')
        planning_lines_to_vertices = planning_menu.addAction(icon,self.tr('Planning Lines to Vertices'), self.run_planning_lines_to_vertices)
        planning_lines_to_vertices.setToolTip('Extract vertices from planning line layer.')
        
        planning_menu.addSeparator()
        
        # calculate mbes coverage
        icon = QIcon(f'{icon_path}/mbes_coverage.png')
        planning_lines_to_vertices = planning_menu.addAction(icon,self.tr('Calculate MBES Coverage'), self.run_calculate_mbes_coverage)
        planning_lines_to_vertices.setToolTip('Calculate approximate MBES coverage for a survey planning line.\n\n'
                                              'Survey settings can be set in the dialog.')
        
        planning_menu.addSeparator()
        
        # export to bridge button
        icon = QIcon(f'{icon_path}/export_to_bridge.png')
        export_to_bridge = planning_menu.addAction(icon,self.tr('Export to Bridge'), self.run_export_to_bridge)
        export_to_bridge.setToolTip('Export planning layer (point or line) to bridge exchange format.')
        
        # setup planning menu
        icon = QIcon(f'{icon_path}/planning_menu.png')
        self.planningAction = QAction(icon, 'Planning', self.iface.mainWindow())
        self.planningAction.setMenu(planning_menu)
        
        self.planningButton = QToolButton()
        self.planningButton.setMenu(planning_menu)
        self.planningButton.setDefaultAction(self.planningAction)
        self.planningButton.setPopupMode(QToolButton.InstantPopup)
        self.tranformToolbar = self.toolbar.addWidget(self.planningButton)
        
        # SETTINGS BUTTON
        icon = f'{icon_path}/settings.png'
        config = self.add_action(icon,
                                    text=self.tr('Settings'),
                                    callback=self.run_settings,
                                    parent=self.iface.mainWindow())
        config.setToolTip('Open the Cruise Tools configuration dialog.')
    
    def unload(self):
        '''Removes the plugin menu item and icon from QGIS GUI.'''
        
        #print "** UNLOAD CruiseTools"
        
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr('&Cruise Tools'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
    
#===============================================================================
#=================================   README   ==================================
#===============================================================================
    
    def run_readme(self):
        '''README'''
        #if not self.pluginIsActive:
        #    self.pluginIsActive = True
        iface.messageBar().pushMessage('Cruise Tools ', 'Awesome and practical Cruise Tools by the Bauernprogrammiererz Fynn & Simon! <3', level=Qgis.Info)
        
        self.readme = ReadmeWindow()
        
        # load README
        with open(os.path.join(self.plugin_dir, 'README'), 'r') as f:
            readmeText = f.read()
        # set text
        self.readme.textEdit.setText(readmeText)
        #self.readme.textEdit.setMarkdown(readmeText) # for future PyQt versions (>5.14)!
        
        # set font
        font = QFont('Courier', 10)
        self.readme.textEdit.setFont(font)
        
        # protect text
        self.readme.textEdit.setReadOnly(True)
        #self.readme.textEdit.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        
        # set 
        layout = QHBoxLayout(self.readme)
        layout.addWidget(self.readme.textEdit)
        self.readme.setLayout(layout)
        self.readme.setWindowTitle('Readme')
        
        self.readme.show()
        
        return
    
#===============================================================================
#===============================   BATHYMETRY   ================================
#===============================================================================
    
    def run_load_bathy(self):
        '''Load Bathymetry'''
        #if not self.pluginIsActive:
        #    self.pluginIsActive = True
        
        # load file twice with style def for color scale and hillshade
        error, result = load_bathy()
        
        # test if grid successfully loaded
        if error:
            iface.messageBar().pushMessage('Cruise Tools ', result, level=Qgis.Critical)
            return
                
        # refresh canvas
        iface.mapCanvas().refresh()
        
        # all done
        iface.messageBar().pushMessage('Cruise Tools ', f'{return_success()}! Grid loaded successfully!', level=Qgis.Success)
        
        return
    
#===============================================================================
    
    def run_export_combo(self):
        '''Export Shaded Bathymetry [Slope + Hillshade]'''
        #if not self.pluginIsActive:
        #    self.pluginIsActive = True
        
        # get active layer from TOC
        active_layer = iface.activeLayer()
        
        # test if a layer is selected
        if active_layer is None:
            iface.messageBar().pushMessage('Cruise Tools ', 'No layer selected', level=Qgis.Critical)
            return
        
        # test if selected layer is a raster layer
        elif active_layer.type() != QgsMapLayerType.RasterLayer:
            iface.messageBar().pushMessage('Cruise Tools ', 'The selected layer is not a RASTER layer', level=Qgis.Critical)
            return
        
        # run function
        error, result = create_combo_shaded(active_layer)
        
        # check success
        if error:
            iface.messageBar().pushMessage('Cruise Tools ', result, level=Qgis.Critical)
            return
        else:
            iface.messageBar().pushMessage('Cruise Tools ', f'{return_success()}! Your combo shaded bathymetry file: {return_file_link(result)}', level=Qgis.Success)
        
        # refresh canvas
        iface.mapCanvas().refresh()
        
        return
    
#===============================================================================
    
    def run_export_hs(self):
        '''Export Shaded Bathymetry [Hillshade]'''
        #if not self.pluginIsActive:
        #    self.pluginIsActive = True
        
        # get active layer from TOC
        active_layer = iface.activeLayer()
        
        # test if a layer is selected
        if active_layer is None:
            iface.messageBar().pushMessage('Cruise Tools ', 'No layer selected', level=Qgis.Critical)
            return
        
        # test if selected layer is a raster layer
        elif active_layer.type() != QgsMapLayerType.RasterLayer:
            iface.messageBar().pushMessage('Cruise Tools ', 'The selected layer is not a RASTER layer', level=Qgis.Critical)
            return
        
        # run function
        error, result = create_hs_shaded(active_layer)
        
        # check success
        if error:
            iface.messageBar().pushMessage('Cruise Tools ', result, level=Qgis.Critical)
            return
        else:
            iface.messageBar().pushMessage('Cruise Tools ', f'{return_success()}! Your hillshaded bathymetry file: {return_file_link(result)}', level=Qgis.Success)
        
        # refresh canvas
        iface.mapCanvas().refresh()
        
        return
    
#===============================================================================
    
    def run_export_slope(self):
        '''Export Shaded Bathymetry [Slope]'''
        #if not self.pluginIsActive:
        #    self.pluginIsActive = True
        
        # get active layer from TOC
        active_layer = iface.activeLayer()
        
        # test if a layer is selected
        if active_layer is None:
            iface.messageBar().pushMessage('Cruise Tools ', 'No layer selected', level=Qgis.Critical)
            return
        
        # test if selected layer is a raster layer
        elif active_layer.type() != QgsMapLayerType.RasterLayer:
            iface.messageBar().pushMessage('Cruise Tools ', 'The selected layer is not a RASTER layer', level=Qgis.Critical)
            return
        
        # run function
        error, result = create_slope_shaded(active_layer)
        
        # check success
        if error:
            iface.messageBar().pushMessage('Cruise Tools ', result, level=Qgis.Critical)
            return
        else:
            iface.messageBar().pushMessage('Cruise Tools ', f'{return_success()}! Your slope shaded bathymetry file: {return_file_link(result)}', level=Qgis.Success)
        
        # refresh canvas
        iface.mapCanvas().refresh()
        
        return
    
#===============================================================================
    
    def run_calculate_raster_coverage(self):
        '''Calculate Raster Coverage'''
        #if not self.pluginIsActive:
        #    self.pluginIsActive = True
        
        # initialize GUI window
        self.rasterCoverage = RasterCoverage()
        self.rasterCoverage.setFixedSize(480,465)
        
        # get available raster layers from project
        layers = QgsProject.instance().mapLayers().values()
        raster_layers = [layer for layer in layers if layer.type() == QgsMapLayer.RasterLayer]
        
        # populate comboBox with raster layers
        self.rasterCoverage.comboBoxInputRaster.clear()
        self.rasterCoverage.comboBoxInputRaster.addItems([layer.name() for layer in raster_layers])
        
        # populate comboBoxInputBand with bands of first raster layer from project
        self.rasterCoverage.comboBoxInputBand.addItems([raster_layers[0].bandName(i+1) for i in range(raster_layers[0].bandCount())])
        
        # get active layer and set it as "INPUT RASTER" if it is a QgsRasterLayer
        active_layer = self.iface.activeLayer()
        if (active_layer != None) and (active_layer.type() == QgsMapLayer.RasterLayer):
            self.rasterCoverage.comboBoxInputRaster.setCurrentText(active_layer.name())
            
            # set alignment for band number input box
            self.rasterCoverage.comboBoxInputBand.clear()
            self.rasterCoverage.comboBoxInputBand.addItems([active_layer.bandName(i+1) for i in range(active_layer.bandCount())])
        
        # show window
        self.rasterCoverage.show()
        
        # update input band option based on selected input raster
        self.rasterCoverage.comboBoxInputRaster.currentTextChanged.connect(self.rc_update_input_bands)
        
        # compute calculation if button "CALCULATE" is clicked
        self.rasterCoverage.pushButtonCalc.clicked.connect(self.rc_on_calculate)
        
        self.rasterCoverage.exec_()
        
        return
    
#===============================================================================
    
    def rc_update_input_bands(self):
        '''Update selectable input bands according to input raster'''
        # clear comboBox
        self.rasterCoverage.comboBoxInputBand.clear()
        # get current input raster
        self.input_raster = QgsProject.instance().mapLayersByName(self.rasterCoverage.comboBoxInputRaster.currentText())[0]
        # get band names of input raster
        bands = [self.input_raster.bandName(i+1) for i in range(self.input_raster.bandCount())]
        # populate comboBox with available bands
        self.rasterCoverage.comboBoxInputBand.addItems(bands)
        
        # clear values
        for field in self.rasterCoverage.groupBoxOutput.children():
            if type(field) == QTextEdit:
                field.clear()
        
        return
    
#===============================================================================
    
    def rc_on_calculate(self):
        '''Perform raster coverage calculation'''
        # get name and layer of input raster
        input_raster = self.rasterCoverage.comboBoxInputRaster.currentText()
        layer = QgsProject.instance().mapLayersByName(input_raster)[0]
        
        # get band number of input raster
        input_band = self.rasterCoverage.comboBoxInputBand.currentIndex() + 1
        
        # run imported function
        error, msg, result = calculate_raster_coverage(layer, input_band)
        if error:
            iface.messageBar().pushMessage('Cruise Tools ', msg, level=Qgis.Critical)
        
        area_m2, coverage_m2, coverage_percentage = result
        area_km2 = area_m2 / (1000*1000)
        coverage_km2 = coverage_m2 / (1000*1000)
        
        # set outputs to textEdit widgets
        self.rasterCoverage.textRasterAreaKilometer.setText(str(round(area_km2,3)))
        self.rasterCoverage.textDataCoverageKilometer.setText(str(round(coverage_km2,3)))
        self.rasterCoverage.textDataCoverageMeter.setText(str(round(coverage_m2,2)))
        self.rasterCoverage.textDataCoveragePercentage.setText(str(round(coverage_percentage*100,2)))
        
        # area of Bremen in km^2
        bremen_area = 419.4
        # set fun fact
        self.rasterCoverage.textDataCoverageBremen.setText(str(round(coverage_km2 / bremen_area, 1)))
        
        # set alignment for all textBoxes
        for field in self.rasterCoverage.groupBoxOutput.children():
            if type(field) == QTextEdit:
                field.setAlignment(Qt.AlignRight)
        
        return
    
#===============================================================================
#================================   CONTOURS   =================================
#===============================================================================
    
    def run_create_contours_1000(self):
        self.run_create_contours(1000)
        return
    
    def run_create_contours_500(self):
        self.run_create_contours(500)
        return
    
    def run_create_contours_100(self):
        self.run_create_contours(100)
        return
    
    def run_create_contours_50(self):
        self.run_create_contours(50)
        return
    
    def run_create_contours_10(self):
        self.run_create_contours(10)
        return
    
    def run_create_contours_5(self):
        self.run_create_contours(5)
        return
    
    def run_create_contours_1(self):
        self.run_create_contours(1)
        return
    
#===============================================================================
    
    def run_create_contours(self,interval):
        '''Create Contours'''
        #if not self.pluginIsActive:
        #    self.pluginIsActive = True
        
        # get active layer from TOC
        active_layer = iface.activeLayer()
        
        # test if a layer is selected
        if active_layer is None:
            iface.messageBar().pushMessage('Cruise Tools ', 'No layer selected', level=Qgis.Critical)
            return
        
        # test if selected layer is a raster layer
        elif active_layer.type() != QgsMapLayerType.RasterLayer:
            iface.messageBar().pushMessage('Cruise Tools ', 'The selected layer is not a RASTER layer', level=Qgis.Critical)
            return
        
        # run function
        error, result = create_contours(active_layer,interval)
        
        # check success
        if error:
            iface.messageBar().pushMessage('Cruise Tools ', result, level=Qgis.Critical)
            return
        else:
            iface.messageBar().pushMessage('Cruise Tools ', f'{return_success()}! Your contours file: {return_file_link(result)}', level=Qgis.Success)
        
        # refresh canvas
        iface.mapCanvas().refresh()
        
        return
    
#===============================================================================
#=================================   VECTOR   ==================================
#===============================================================================
    
    def run_write_point_coordinates(self):
        '''Write Point Coordinates'''
        #if not self.pluginIsActive:
        #    self.pluginIsActive = True
        
        # get active layer from TOC
        active_layer = iface.activeLayer()
        
        # test if a layer is selected
        if active_layer is None:
            iface.messageBar().pushMessage('Cruise Tools ', 'No layer selected', level=Qgis.Critical)
            return
        
        # test if selected layer is a vector layer
        elif active_layer.type() != QgsMapLayerType.VectorLayer:
            iface.messageBar().pushMessage('Cruise Tools ', 'The selected layer is not a VECTOR layer', level=Qgis.Critical)
            return
        
        # test if selected layer is a point feature layer
        elif active_layer.geometryType() != QgsWkbTypes.PointGeometry:
            iface.messageBar().pushMessage('Cruise Tools ', 'The selected layer is not a POINT layer', level=Qgis.Critical)
            return
        
        # test if selected layer is a point feature layer
        elif active_layer.geometryType() == QgsWkbTypes.MultiPoint:
            iface.messageBar().pushMessage('Cruise Tools ', 'Sorry, this tool does not work with MultiPoint layers', level=Qgis.Critical)
            return
        
        # run function
        error,result = write_point_coordinates(active_layer)
        
        # check success
        if error:
            iface.messageBar().pushMessage('Cruise Tools ', result, level=Qgis.Critical)
            return
        else:
            iface.messageBar().pushMessage('Cruise Tools ', f'{return_success()}! Coordinates are in!', level=Qgis.Success)
        
        # refresh canvas
        iface.mapCanvas().refresh()
        
        return
    
#===============================================================================
    
    def run_write_line_length(self):
        '''Write Line Length'''
        #if not self.pluginIsActive:
        #    self.pluginIsActive = True
        
        # Get active layer from TOC
        active_layer = iface.activeLayer()
        
        # test if a layer is selected
        if active_layer is None:
            iface.messageBar().pushMessage('Cruise Tools ', 'No layer selected', level=Qgis.Critical)
            return
        
        # test if selected layer is a vector layer
        elif active_layer.type() != QgsMapLayerType.VectorLayer:
            iface.messageBar().pushMessage('Cruise Tools ', 'The selected layer is not a VECTOR layer', level=Qgis.Critical)
            return
        
        # test if selected layer is a line feature layer
        elif active_layer.geometryType() != QgsWkbTypes.LineGeometry:
            iface.messageBar().pushMessage('Cruise Tools ', 'The selected layer is not a LINE layer', level=Qgis.Critical)
            return
        
        # run function
        error,result = write_line_length(active_layer,m=True,nm=True)
        
        # check success
        if error:
            iface.messageBar().pushMessage('Cruise Tools ', result, level=Qgis.Critical)
            return
        else:
            iface.messageBar().pushMessage('Cruise Tools ', f'{return_success()}! Lengths are in!', level=Qgis.Success)
        
        # refresh canvas
        iface.mapCanvas().refresh()
        
        return
    
#===============================================================================
    
    def run_write_polygon_area(self):
        '''Write Line Length'''
        #if not self.pluginIsActive:
        #    self.pluginIsActive = True
        
        # Get active layer from TOC
        active_layer = iface.activeLayer()
        
        # test if a layer is selected
        if active_layer is None:
            iface.messageBar().pushMessage('Cruise Tools ', 'No layer selected', level=Qgis.Critical)
            return
        
        # test if selected layer is a vector layer
        elif active_layer.type() != QgsMapLayerType.VectorLayer:
            iface.messageBar().pushMessage('Cruise Tools ', 'The selected layer is not a VECTOR layer', level=Qgis.Critical)
            return
        
        # test if selected layer is a line feature layer
        elif active_layer.geometryType() != QgsWkbTypes.PolygonGeometry:
            iface.messageBar().pushMessage('Cruise Tools ', 'The selected layer is not a POLYGON layer', level=Qgis.Critical)
            return
        
        # run function
        error,result = write_polygon_area(active_layer,m2=True,km2=True)
        
        # check success
        if error:
            iface.messageBar().pushMessage('Cruise Tools ', result, level=Qgis.Critical)
            return
        else:
            iface.messageBar().pushMessage('Cruise Tools ', f'{return_success()}! Areas are in!', level=Qgis.Success)
        
        # refresh canvas
        iface.mapCanvas().refresh()
        
        return
    
#===============================================================================
    
    def run_swap_vectors(self):
        '''Swap Vectors'''
        #if not self.pluginIsActive:
        #    self.pluginIsActive = True
        
        # Get active layer from TOC
        active_layer = iface.activeLayer()
        
        # test if a layer is selected
        if active_layer is None:
            iface.messageBar().pushMessage('Cruise Tools ', 'No layer selected', level=Qgis.Critical)
            return
        
        # test if selected layer is a vector layer
        elif active_layer.type() != QgsMapLayerType.VectorLayer:
            iface.messageBar().pushMessage('Cruise Tools ', 'The selected layer is not a VECTOR layer', level=Qgis.Critical)
            return
        
        # test if selected layer is a line feature layer
        elif active_layer.geometryType() != QgsWkbTypes.LineGeometry:
            iface.messageBar().pushMessage('Cruise Tools ', 'The selected layer is not a line layer', level=Qgis.Critical)
            return
        
        # run function
        error,result = swap_vectors(active_layer,selected=True)
        
        # check success
        if error:
            iface.messageBar().pushMessage('Cruise Tools ', result, level=Qgis.Critical)
            return
        else:
            iface.messageBar().pushMessage('Cruise Tools ', f'{return_success()}! Vectors swapped successfully!', level=Qgis.Success)
        
        # refresh canvas
        iface.mapCanvas().refresh()
        
        return
    
#===============================================================================
#================================   PLANNING   =================================
#===============================================================================
    
    def run_create_point_planning_file(self):
        '''Create Point Planning File'''
        #if not self.pluginIsActive:
        #    self.pluginIsActive = True
        
        # run function
        error, result = create_point_planning_file()
        
        # check success
        if error:
            iface.messageBar().pushMessage('Cruise Tools ', result, level=Qgis.Critical)
            return
        else:
            iface.messageBar().pushMessage('Cruise Tools ', f'{return_success()}! Your Point Planning file: {return_file_link(result)}', level=Qgis.Success)
        
        # refresh canvas
        iface.mapCanvas().refresh()
        
        return
    
#===============================================================================
    
    def run_create_line_planning_file(self):
        '''Create Line Planning File'''
        #if not self.pluginIsActive:
        #    self.pluginIsActive = True
        
        # run function
        error, result = create_line_planning_file()
        
        # check success
        if error:
            iface.messageBar().pushMessage('Cruise Tools ', result, level=Qgis.Critical)
            return
        else:
            iface.messageBar().pushMessage('Cruise Tools ', f'{return_success()}! Your Line Planning file: {return_file_link(result)}', level=Qgis.Success)
        
        # refresh canvas
        iface.mapCanvas().refresh()
        
        return
    
#===============================================================================
    
    def run_planning_lines_to_vertices(self):
        '''Convert Lines to Vertices'''
        #if not self.pluginIsActive:
        #    self.pluginIsActive = True
        
        # Get active layer from TOC
        active_layer = iface.activeLayer()
        
        # test if a layer is selected
        if active_layer is None:
            iface.messageBar().pushMessage('Cruise Tools ', 'No layer selected', level=Qgis.Critical)
            return
        
        # test if selected layer is a vector layer
        elif active_layer.type() != QgsMapLayerType.VectorLayer:
            iface.messageBar().pushMessage('Cruise Tools ', 'The selected layer is not a VECTOR layer', level=Qgis.Critical)
            return
        
        # test if selected layer is a point feature layer
        elif active_layer.geometryType() != QgsWkbTypes.LineGeometry:
            iface.messageBar().pushMessage('Cruise Tools ', 'The selected layer is not a LINE layer', level=Qgis.Critical)
            return
        
        # run function
        error, result = planning_lines_to_vertices(active_layer)
        
        # check success
        if error:
            iface.messageBar().pushMessage('Cruise Tools ', result, level=Qgis.Critical)
            return
        else:
            iface.messageBar().pushMessage('Cruise Tools ', f'{return_success()}! Your Vertices file: {return_file_link(result)}', level=Qgis.Success)
        
        # refresh canvas
        iface.mapCanvas().refresh()
        
        return
    
#===============================================================================
    
    def run_calculate_mbes_coverage(self):
        '''Calculate MBES Coverage'''
        #if not self.pluginIsActive:
        #    self.pluginIsActive = True
        
        # initialize GUI window
        self.mbes_coverage = MBEScoverage()
        self.mbes_coverage.setFixedSize(480,405)
        
        # get available raster layers from project
        layers = QgsProject.instance().mapLayers().values()
        line_layers = [line for line in layers if (line.type() == QgsMapLayerType.VectorLayer) and (line.geometryType() == QgsWkbTypes.GeometryType.LineGeometry)]
        raster_layers = [raster for raster in layers if raster.type() == QgsMapLayer.RasterLayer]
        
        # QgsMapLayerType.VectorLayer
        
        # populate comboBox with line layers
        self.mbes_coverage.comboBoxInputPolyline.clear()
        self.mbes_coverage.comboBoxInputPolyline.addItems([layer.name() for layer in line_layers])
        
        # get active layer and set it as "INPUT POLYLINE" if it is a LineGeometry
        active_layer = self.iface.activeLayer()
        
        # test if a line vector layer is selected
        if (active_layer != None) and (active_layer.type() == QgsMapLayerType.VectorLayer) and (active_layer.geometryType() == QgsWkbTypes.LineGeometry):
            # if yes, set as 'INPUT POLYLINE'
            self.mbes_coverage.comboBoxInputPolyline.setCurrentText(active_layer.name())
        
        # populate comboBox with raster layers
        self.mbes_coverage.comboBoxInputRaster.clear()
        self.mbes_coverage.comboBoxInputRaster.addItems([layer.name() for layer in raster_layers])
        
        # if user default input raster is set and still present in the project, set it as 'INPUT RASTER'
        try:
            self.mbes_coverage.comboBoxInputRaster.setCurrentText(self.mbes_coverage_raster.name())
        except (AttributeError, NameError, RuntimeError):
            pass
        
        
        # populate comboBoxInputBand with bands of first raster layer from project
        self.mbes_coverage.comboBoxInputBand.addItems([raster_layers[0].bandName(i+1) for i in range(raster_layers[0].bandCount())])
                
        # populate spinBox with default swath angle
        self.mbes_coverage.spinBoxSwathAngleNadir.setRange(5,80)
        self.mbes_coverage.spinBoxSwathAngleNadir.setValue(65)
        self.mbes_coverage.spinBoxSwathAngleTotal.setValue(130)
        self.mbes_coverage.spinBoxSwathAngleTotal.setRange(10,160)
        self.mbes_coverage.spinBoxSwathAngleTotal.setSingleStep(2)
        self.mbes_coverage.spinBoxSwathAngleTotal.setValue(130)
        
        # link both spinBoxes so if one gets updated the other changes
        self.mbes_coverage.spinBoxSwathAngleNadir.valueChanged.connect(self.mbes_update_swath_angle_total)
        self.mbes_coverage.spinBoxSwathAngleTotal.valueChanged.connect(self.mbes_update_swath_angle_nadir)
        
        # show window
        self.mbes_coverage.show()      
        
        # compute calculation if button "CALCULATE" is clicked
        self.mbes_coverage.pushButtonCalc.clicked.connect(self.mbes_on_calculate)
        
        return
    
    def mbes_update_swath_angle_total(self):
        '''Update total swath angle based on swath angle from nadir input'''
        value = self.mbes_coverage.spinBoxSwathAngleNadir.value()
        self.mbes_coverage.spinBoxSwathAngleTotal.setValue(value * 2)
    
    def mbes_update_swath_angle_nadir(self):
        '''Update swath angle from nadir based on total swath angle input'''
        value = self.mbes_coverage.spinBoxSwathAngleTotal.value()
        self.mbes_coverage.spinBoxSwathAngleNadir.setValue(value / 2)
    
    def mbes_on_calculate(self):
        '''Perform MBES coverage calculation'''
        # get name and layer of input polyline
        input_line = self.mbes_coverage.comboBoxInputPolyline.currentText()
        layer_line = QgsProject.instance().mapLayersByName(input_line)[0]
        
        # get name and layer of input raster
        input_raster = self.mbes_coverage.comboBoxInputRaster.currentText()
        layer_raster = QgsProject.instance().mapLayersByName(input_raster)[0]
        
        # set raster input layer as user default for next time
        self.mbes_coverage_raster = layer_raster
        
        # get band number of input raster
        input_band = self.mbes_coverage.comboBoxInputBand.currentIndex() + 1
        
        # get swath angle
        swath_angle_nadir = self.mbes_coverage.spinBoxSwathAngleNadir.value()
        swath_angle_total = self.mbes_coverage.spinBoxSwathAngleTotal.value()
        if not swath_angle_nadir * 2 == swath_angle_total:
            iface.messageBar().pushMessage('Cruise Tools ', 'The given swath angles are not compatible. Please check input!', level=Qgis.Critical)
        
        error, result = calculate_mbes_coverage(layer_line, layer_raster, input_band, swath_angle_total)
        
        # check success
        if error:
            iface.messageBar().pushMessage('Cruise Tools ', result, level=Qgis.Critical)
            return
        else:
            iface.messageBar().pushMessage('Cruise Tools ', f'{return_success()}! Your MBES coverage has been calculated!', level=Qgis.Success)
        
        self.mbes_coverage.close()
        
        return
    
#===============================================================================
    
    def run_export_to_bridge(self):
        '''Export to Bridge'''
        #if not self.pluginIsActive:
        #    self.pluginIsActive = True
        
        # Get active layer from TOC
        active_layer = iface.activeLayer()
        
        # test if a layer is selected
        if active_layer is None:
            iface.messageBar().pushMessage('Cruise Tools ', 'No layer selected', level=Qgis.Critical)
            return
        
        # test if selected layer is a vector layer
        elif active_layer.type() != QgsMapLayerType.VectorLayer:
            iface.messageBar().pushMessage('Cruise Tools ', 'The selected layer is not a VECTOR layer', level=Qgis.Critical)
            return
        
        # if point then export_points, if line then export_lines
        if active_layer.geometryType() == QgsWkbTypes.PointGeometry:
            error, result = export_points_to_bridge(active_layer)
        elif active_layer.geometryType() == QgsWkbTypes.LineGeometry:
            error, result = export_lines_to_bridge(active_layer)
        # if something else, cancel
        else:
            iface.messageBar().pushMessage('Cruise Tools ', 'The selected layer is not a POINT or LINE layer', level=Qgis.Critical)
            return
        
        # check success
        if error:
            iface.messageBar().pushMessage('Cruise Tools ', result, level=Qgis.Critical)
            return
        else:
            iface.messageBar().pushMessage('Cruise Tools ', f'{return_success()}! Your exported file: {return_file_link(result)}', level=Qgis.Success)
        
        # refresh canvas
        iface.mapCanvas().refresh()
        
        return
    
#===============================================================================
#================================   SETTINGS   =================================
#===============================================================================
    
    def run_settings(self):
        '''SETTINGS'''
        # open settings GUI
        if self.first_start == True:
            self.first_start = False
            self.dlg = SettingsWindowDialog()
        # fix window size
        self.dlg.setFixedSize(480,550)
        
        # read settings
        config = read_settings()
        
        # populate VESSEL comboBox
        self.dlg.comboBoxVessel.clear()
        vessels = ['default','RV Sonne','RV Maria S. Merian','RV Polarstern']
        self.dlg.comboBoxVessel.addItems(vessels)
        self.dlg.comboBoxVessel.setCurrentText(config['VESSEL']['vessel'])
        
        # populate COMPRESSION comboBox
        self.dlg.comboBoxCompression.clear()
        compression_options = ['DEFLATE','LZW','NONE']
        self.dlg.comboBoxCompression.addItems(compression_options)
        self.dlg.comboBoxCompression.setCurrentText(config['COMPRESSION']['type'])
        
        # populate COLORS comboBox
        self.dlg.comboBoxColors.clear()
        colors_options = ['Haxby','Blues','Rainbow']
        self.dlg.comboBoxColors.addItems(colors_options)
        self.dlg.comboBoxColors.setCurrentText(config['BATHYMETRY']['colors'])
        
        # BATHYMETRY DEPTH RANGE
        self.dlg.spinBoxMaximum.setValue(int(config['BATHYMETRY']['max']))
        self.dlg.spinBoxMinimum.setValue(int(config['BATHYMETRY']['min']))
        
        # show GUI
        self.dlg.show()
        
        # check if GUI was close using "OK" button
        result = self.dlg.exec_()
        
        # process triggered by "OK" button
        if result:
            # get selected vessel
            selected_vessel = self.dlg.comboBoxVessel.currentText()
            # get selected compression type
            selected_compression = self.dlg.comboBoxCompression.currentText()
            # get selected colors
            selected_colors = self.dlg.comboBoxColors.currentText()
            # get minimum & maximum depth values for bathymetry colormap
            max_bathy = self.dlg.spinBoxMaximum.value()
            min_bathy = self.dlg.spinBoxMinimum.value()
            
            # initialize config file
            config = configparser.ConfigParser()
            config['VESSEL'] = {'vessel' : selected_vessel}
            config['COMPRESSION'] = {'type' : selected_compression}
            config['BATHYMETRY'] = {'colors' : selected_colors, 
                                    'max' : max_bathy,
                                    'min' : min_bathy}
            
            # write config file
            write_settings(config)
            
            # show message
            iface.messageBar().pushMessage('Cruise Tools ', f'{return_success()}! Saved settings successfully!', level=Qgis.Success)
        
        return
