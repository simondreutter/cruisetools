# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CruiseTools
                                 A QGIS plugin
 Tool box for various GIS tasks for cruise planning, etc.
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
"""
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
from .auxiliary_tools import *
from .bathymetry import *
from .contours import *
from .vector import *
from .planning import *
from .config import *

# Import GUI
from .ui.RasterCoverage import RasterCoverage
from .ui.SettingsWindow_dialog import SettingsWindowDialog
from .ui.ReadmeWindow import ReadmeWindow

class CruiseTools:
	"""QGIS Plugin Implementation."""
	def __init__(self, iface):
		"""Constructor.
		
		:param iface: An interface instance that will be passed to this class
			which provides the hook by which you can manipulate the QGIS
			application at run time.
		:type iface: QgsInterface
		"""
		# Save reference to the QGIS interface
		self.iface = iface
		
		# initialize plugin directory
		self.plugin_dir = os.path.dirname(__file__)
		
		# initialize locale
		locale = QSettings().value('locale/userLocale')[0:2]
		locale_path = os.path.join(
			self.plugin_dir,
			'i18n',
			'CruiseTools_{}.qm'.format(locale))
		
		if os.path.exists(locale_path):
			self.translator = QTranslator()
			self.translator.load(locale_path)
			
			if qVersion() > '4.3.3':
				QCoreApplication.installTranslator(self.translator)
		
		# Declare instance attributes
		self.actions = []
		self.menu = self.tr(u'&Cruise Tools')
		# TODO: We are going to let the user set this up in a future iteration
		self.toolbar = self.iface.addToolBar(u'CruiseTools')
		self.toolbar.setObjectName(u'CruiseTools')
		
		#print "** INITIALIZING CruiseTools"
		
		self.pluginIsActive = False
		self.dockwidget = None
		
		init_settings()
	
	# noinspection PyMethodMayBeStatic
	def tr(self, message):
		"""Get the translation for a string using Qt translation API.
		
		We implement this ourselves since we do not inherit QObject.
		
		:param message: String for translation.
		:type message: str, QString
		
		:returns: Translated version of message.
		:rtype: QString
		"""
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
		"""Add a toolbar icon to the toolbar.
		
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
		"""
		
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
		"""Create the menu entries and toolbar icons inside the QGIS GUI."""
		# get first start indication
		self.first_start = True	
		
		# README BUTTON
		icon = QIcon(':/plugins/cruisetools/images/icon.png')
		#icon = ':/plugins/cruisetools/images/icon.png'
		readme = self.add_action(icon,
									text=self.tr(u'Cruise Tools'),
									callback=self.run,
									parent=self.iface.mainWindow())
		
		
		# BATHYMETRY SUBMENU
		bathy_menu = QMenu()
		
		# load bathymetry button
		icon = QIcon(':/plugins/cruisetools/images/load_bathy.png')
		load_bathy = bathy_menu.addAction(icon,self.tr(u'Load Bathymetry'), self.run_load_bathy)
		
		# export bathymetry submenu
		icon = QIcon(':/plugins/cruisetools/images/export_bathy.png')
		export_bathy_submenu = bathy_menu.addMenu(icon,self.tr(u'Export Shaded Bathymetry'))
		
		# export bathymetry buttons
		icon = QIcon(':/plugins/cruisetools/images/export_combo.png')
		export_bathy_combo = export_bathy_submenu.addAction(icon,self.tr(u'Slope + Hillshade'), self.run_export_combo)
		icon = QIcon(':/plugins/cruisetools/images/export_hs.png')
		export_bathy_hs = export_bathy_submenu.addAction(icon,self.tr(u'Hillshade'), self.run_export_hs)
		icon = QIcon(':/plugins/cruisetools/images/export_slope.png')
		export_bathy_slope = export_bathy_submenu.addAction(icon,self.tr(u'Slope'), self.run_export_slope)
		
		bathy_menu.addSeparator()
		
		# raster coverage button
		icon = QIcon(':/plugins/cruisetools/images/raster_coverage.png')
		load_bathy = bathy_menu.addAction(icon,self.tr(u'Calculate Raster Coverage'), self.run_calculate_raster_coverage)
		
		# setup bathymetry menu
		icon = QIcon(':/plugins/cruisetools/images/bathy_menu.png')
		self.bathyAction = QAction(icon, 'Bathymetry', self.iface.mainWindow())
		self.bathyAction.setMenu(bathy_menu)
		
		self.bathyButton = QToolButton()
		self.bathyButton.setMenu(bathy_menu)
		self.bathyButton.setDefaultAction(self.bathyAction)
		self.bathyButton.setPopupMode(QToolButton.InstantPopup)
		self.tranformToolbar = self.toolbar.addWidget(self.bathyButton)
		
		
		# CONTOURS SUBMENU
		contour_menu = QMenu()
		
		icon = QIcon(':/plugins/cruisetools/images/create_contours_1000.png')
		create_contours_1000m = contour_menu.addAction(icon,self.tr(u'1000 m'), self.run_create_contours_1000)
		icon = QIcon(':/plugins/cruisetools/images/create_contours_500.png')
		create_contours_500m = contour_menu.addAction(icon,self.tr(u'500 m'), self.run_create_contours_500)
		icon = QIcon(':/plugins/cruisetools/images/create_contours_100.png')
		create_contours_100m = contour_menu.addAction(icon,self.tr(u'100 m'), self.run_create_contours_100)
		icon = QIcon(':/plugins/cruisetools/images/create_contours_50.png')
		create_contours_50m = contour_menu.addAction(icon,self.tr(u'50 m'), self.run_create_contours_50)
		icon = QIcon(':/plugins/cruisetools/images/create_contours_10.png')
		create_contours_10m = contour_menu.addAction(icon,self.tr(u'10 m'), self.run_create_contours_10)
		icon = QIcon(':/plugins/cruisetools/images/create_contours_5.png')
		create_contours_5m = contour_menu.addAction(icon,self.tr(u'5 m'), self.run_create_contours_5)
		icon = QIcon(':/plugins/cruisetools/images/create_contours_1.png')
		create_contours_1m = contour_menu.addAction(icon,self.tr(u'1 m'), self.run_create_contours_1)
		
		icon = QIcon(':/plugins/cruisetools/images/contours_menu.png')
		self.contourAction = QAction(icon, 'Create Contours', self.iface.mainWindow())
		self.contourAction.setMenu(contour_menu)
		
		self.contourButton = QToolButton()
		self.contourButton.setMenu(contour_menu)
		self.contourButton.setDefaultAction(self.contourAction)
		self.contourButton.setPopupMode(QToolButton.InstantPopup)
		self.tranformToolbar = self.toolbar.addWidget(self.contourButton)
		
		# VECTOR SUBMENU
		vector_menu = QMenu()
		
		icon = QIcon(':/plugins/cruisetools/images/write_point_coordinates.png')
		write_point_coordinates = vector_menu.addAction(icon,self.tr(u'Write Point Coordinates'), self.run_write_point_coordinates)
		icon = QIcon(':/plugins/cruisetools/images/write_line_length.png')
		write_line_length = vector_menu.addAction(icon,self.tr(u'Write Line Length'), self.run_write_line_length)
		icon = QIcon(':/plugins/cruisetools/images/write_polygon_area.png')
		write_line_length = vector_menu.addAction(icon,self.tr(u'Write Polygon Area'), self.run_write_polygon_area)
		icon = QIcon(':/plugins/cruisetools/images/swap_vectors.png')
		swap_vectors = vector_menu.addAction(icon,self.tr(u'Swap Vectors'), self.run_sv)		
		
		icon = QIcon(':/plugins/cruisetools/images/vector_menu.png')
		self.vectorAction = QAction(icon, 'Vector', self.iface.mainWindow())
		self.vectorAction.setMenu(vector_menu)
		
		self.vectorButton = QToolButton()
		self.vectorButton.setMenu(vector_menu)
		self.vectorButton.setDefaultAction(self.vectorAction)
		self.vectorButton.setPopupMode(QToolButton.InstantPopup)
		self.tranformToolbar = self.toolbar.addWidget(self.vectorButton)
		
		# PLANNING SUBMENU
		planning_menu = QMenu()
		
		icon = QIcon(':/plugins/cruisetools/images/create_point_planning.png')
		create_point_planning_file = planning_menu.addAction(icon,self.tr(u'Create Point Planning File'), self.run_create_point_planning_file)
		icon = QIcon(':/plugins/cruisetools/images/create_line_planning.png')
		create_line_planning_file = planning_menu.addAction(icon,self.tr(u'Create Line Planning File'), self.run_create_line_planning_file)
		icon = QIcon(':/plugins/cruisetools/images/create_line_vertices.png')
		planning_lines_to_vertices = planning_menu.addAction(icon,self.tr(u'Planning Lines to Vertices'), self.run_planning_lines_to_vertices)
		planning_menu.addSeparator()
		icon = QIcon(':/plugins/cruisetools/images/export_to_bridge.png')
		export_to_bridge = planning_menu.addAction(icon,self.tr(u'Export to Bridge'), self.run_export_to_bridge)
		
		icon = QIcon(':/plugins/cruisetools/images/planning_menu.png')
		self.planningAction = QAction(icon, 'Planning', self.iface.mainWindow())
		self.planningAction.setMenu(planning_menu)
		
		self.planningButton = QToolButton()
		self.planningButton.setMenu(planning_menu)
		self.planningButton.setDefaultAction(self.planningAction)
		self.planningButton.setPopupMode(QToolButton.InstantPopup)
		self.tranformToolbar = self.toolbar.addWidget(self.planningButton)
		
		# SETTINGS BUTTON
		icon = ':/plugins/cruisetools/images/settings.png'
		config = self.add_action(icon,
									text=self.tr(u'Settings'),
									callback=self.run_settings,
									parent=self.iface.mainWindow())
	
	def unload(self):
		"""Removes the plugin menu item and icon from QGIS GUI."""
		
		#print "** UNLOAD CruiseTools"
		
		for action in self.actions:
			self.iface.removePluginMenu(
				self.tr(u'&Cruise Tools'),
				action)
			self.iface.removeToolBarIcon(action)
		# remove the toolbar
		del self.toolbar
	
	def run(self):
		"""README"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		iface.messageBar().pushMessage(u'Cruise Tools ', u'Awesome and practical Cruise Tools by the Bauernprogrammiererz Fynn & Simon! <3', level=Qgis.Info)
		
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
	
	def run_load_bathy(self):
		"""Load Bathymetry"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
		# load file twice with style def for color scale and hillshade
		error, result = load_bathy()
		
		# test if grid successfully loaded
		if error:
			iface.messageBar().pushMessage(u'Cruise Tools ', result, level=Qgis.Critical)
			return
				
		# refresh canvas
		iface.mapCanvas().refresh()
		
		# all done
		iface.messageBar().pushMessage(u'Cruise Tools ', u'{}! Grid loaded successfully!'.format(return_success()), level=Qgis.Success)
		
		return
	
	def run_export_combo(self):
		"""Export Shaded Bathymetry [Slope + Hillshade]"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
		# get active layer from TOC
		active_layer = iface.activeLayer()
		
		# test if a layer is selected
		if active_layer is None:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'No layer selected', level=Qgis.Critical)
			return
		
		# test if selected layer is a raster layer
		elif active_layer.type() != QgsMapLayerType.RasterLayer:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'The selected layer is not a RASTER layer', level=Qgis.Critical)
			return
		
		# run function
		error, result = create_combo_shaded(active_layer)
		
		# test success
		if error:
			iface.messageBar().pushMessage(u'Cruise Tools ', result, level=Qgis.Critical)
			return
		else:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'{}! Your combo shaded bathymetry file: {}'.format(return_success(),return_file_link(result)), level=Qgis.Success)
		
		# refresh canvas
		iface.mapCanvas().refresh()
		
		return
	
	def run_export_hs(self):
		"""Export Shaded Bathymetry [Hillshade]"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
		# get active layer from TOC
		active_layer = iface.activeLayer()
		
		# test if a layer is selected
		if active_layer is None:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'No layer selected', level=Qgis.Critical)
			return
		
		# test if selected layer is a raster layer
		elif active_layer.type() != QgsMapLayerType.RasterLayer:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'The selected layer is not a RASTER layer', level=Qgis.Critical)
			return
		
		# run function
		error, result = create_hs_shaded(active_layer)
		
		# test success
		if error:
			iface.messageBar().pushMessage(u'Cruise Tools ', result, level=Qgis.Critical)
			return
		else:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'{}! Your hillshaded bathymetry file: {}'.format(return_success(),return_file_link(result)), level=Qgis.Success)
		
		# refresh canvas
		iface.mapCanvas().refresh()
		
		return
	
	def run_export_slope(self):
		"""Export Shaded Bathymetry [Slope]"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
		# get active layer from TOC
		active_layer = iface.activeLayer()
		
		# test if a layer is selected
		if active_layer is None:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'No layer selected', level=Qgis.Critical)
			return
		
		# test if selected layer is a raster layer
		elif active_layer.type() != QgsMapLayerType.RasterLayer:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'The selected layer is not a RASTER layer', level=Qgis.Critical)
			return
		
		# run function
		error, result = create_slope_shaded(active_layer)
		
		# test success
		if error:
			iface.messageBar().pushMessage(u'Cruise Tools ', result, level=Qgis.Critical)
			return
		else:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'{}! Your slope shaded bathymetry file: {}'.format(return_success(),return_file_link(result)), level=Qgis.Success)
		
		# refresh canvas
		iface.mapCanvas().refresh()
		
		return
	
	def run_calculate_raster_coverage(self):
		"""Calculte Raster Coverage"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
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
		if active_layer.type() == QgsMapLayer.RasterLayer:
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
	
	def rc_update_input_bands(self):
		"""Update selectable input bands according to input raster"""
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
	
	def rc_on_calculate(self):
		"""Perform raster coverage calculation"""
		# get name and layer of input raster
		input_raster = self.rasterCoverage.comboBoxInputRaster.currentText()
		lyr = QgsProject.instance().mapLayersByName(input_raster)[0]
		
		# get band number of input raster
		input_band = self.rasterCoverage.comboBoxInputBand.currentIndex() + 1
		
		# run imported function
		area_m2, coverage_m2, coverage_percentage = calculate_raster_coverage(lyr, input_band)
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
	
	def run_create_contours(self,interval):
		"""Create Contours"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
		# get active layer from TOC
		active_layer = iface.activeLayer()
		
		# test if a layer is selected
		if active_layer is None:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'No layer selected', level=Qgis.Critical)
			return
		
		# test if selected layer is a raster layer
		elif active_layer.type() != QgsMapLayerType.RasterLayer:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'The selected layer is not a RASTER layer', level=Qgis.Critical)
			return
		
		# run function
		error, result = create_contours(active_layer,interval)
		
		# test success
		if error:
			iface.messageBar().pushMessage(u'Cruise Tools ', result, level=Qgis.Critical)
			return
		else:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'{}! Your contours file: {}'.format(return_success(),return_file_link(result)), level=Qgis.Success)
		
		# refresh canvas
		iface.mapCanvas().refresh()
		
		return
	
	def run_write_point_coordinates(self):
		"""Write Point Coordinates"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
		# get active layer from TOC
		active_layer = iface.activeLayer()
		
		# test if a layer is selected
		if active_layer is None:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'No layer selected', level=Qgis.Critical)
			return
		
		# test if selected layer is a vector layer
		elif active_layer.type() != QgsMapLayerType.VectorLayer:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'The selected layer is not a VECTOR layer', level=Qgis.Critical)
			return
		
		# test if selected layer is a point feature layer
		elif active_layer.geometryType() != QgsWkbTypes.PointGeometry:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'The selected layer is not a POINT layer', level=Qgis.Critical)
			return
		
		# run function
		error,result = write_point_coordinates(active_layer)
		
		# test success
		if error:
			iface.messageBar().pushMessage(u'Cruise Tools ', result, level=Qgis.Critical)
			return
		else:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'{}! Coordinates are in!'.format(return_success()), level=Qgis.Success)
		
		# refresh canvas
		iface.mapCanvas().refresh()
		
		return
	
	def run_write_line_length(self):
		"""Write Line Length"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
		# Get active layer from TOC
		active_layer = iface.activeLayer()
		
		# test if a layer is selected
		if active_layer is None:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'No layer selected', level=Qgis.Critical)
			return
		
		# test if selected layer is a vector layer
		elif active_layer.type() != QgsMapLayerType.VectorLayer:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'The selected layer is not a VECTOR layer', level=Qgis.Critical)
			return
		
		# test if selected layer is a line feature layer
		elif active_layer.geometryType() != QgsWkbTypes.LineGeometry:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'The selected layer is not a LINE layer', level=Qgis.Critical)
			return
		
		# run function
		error,result = write_line_length(active_layer,True,True)
		
		# test success
		if error:
			iface.messageBar().pushMessage(u'Cruise Tools ', result, level=Qgis.Critical)
			return
		else:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'{}! Lengths are in!'.format(return_success()), level=Qgis.Success)
		
		# refresh canvas
		iface.mapCanvas().refresh()
		
		return
	
	def run_write_polygon_area(self):
		"""Write Line Length"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
		# Get active layer from TOC
		active_layer = iface.activeLayer()
		
		# test if a layer is selected
		if active_layer is None:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'No layer selected', level=Qgis.Critical)
			return
		
		# test if selected layer is a vector layer
		elif active_layer.type() != QgsMapLayerType.VectorLayer:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'The selected layer is not a VECTOR layer', level=Qgis.Critical)
			return
		
		# test if selected layer is a line feature layer
		elif active_layer.geometryType() != QgsWkbTypes.PolygonGeometry:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'The selected layer is not a POLYGON layer', level=Qgis.Critical)
			return
		
		# run function
		error,result = write_polygon_area(active_layer,True,True)
		
		# test success
		if error:
			iface.messageBar().pushMessage(u'Cruise Tools ', result, level=Qgis.Critical)
			return
		else:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'{}! Areas are in!'.format(return_success()), level=Qgis.Success)
		
		# refresh canvas
		iface.mapCanvas().refresh()
		
		return
	
	def run_sv(self):
		"""Swap Vectors"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
		# Get active layer from TOC
		active_layer = iface.activeLayer()
		
		# test if a layer is selected
		if active_layer is None:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'No layer selected', level=Qgis.Critical)
			return
		
		# test if selected layer is a vector layer
		elif active_layer.type() != QgsMapLayerType.VectorLayer:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'The selected layer is not a VECTOR layer', level=Qgis.Critical)
			return
		
		# test if selected layer is a line feature layer
		elif active_layer.geometryType() != QgsWkbTypes.LineGeometry:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'The selected layer is not a line layer', level=Qgis.Critical)
			return
		
		# run function
		error,result = swap_vectors(active_layer)
		
		# test success
		if error:
			iface.messageBar().pushMessage(u'Cruise Tools ', result, level=Qgis.Critical)
			return
		else:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'{}! Vectors swapped successfully!'.format(return_success()), level=Qgis.Success)
		
		# refresh canvas
		iface.mapCanvas().refresh()
		
		return
	
	def run_create_point_planning_file(self):
		"""Create Point Planning File"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
		# run function
		error, result = create_point_planning_file()
		
		# test success
		if error:
			iface.messageBar().pushMessage(u'Cruise Tools ', result, level=Qgis.Critical)
			return
		else:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'{}! Your Point Planning file: {}'.format(return_success(),return_file_link(result)), level=Qgis.Success)
		
		# refresh canvas
		iface.mapCanvas().refresh()
		
		return
	
	def run_create_line_planning_file(self):
		"""Create Line Planning File"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
		# run function
		error, result = create_line_planning_file()
		
		# test success
		if error:
			iface.messageBar().pushMessage(u'Cruise Tools ', result, level=Qgis.Critical)
			return
		else:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'{}! Your Line Planning file: {}'.format(return_success(),return_file_link(result)), level=Qgis.Success)
		
		# refresh canvas
		iface.mapCanvas().refresh()
		
		return
	
	def run_planning_lines_to_vertices(self):
		"""Convert Lines to Vertices"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
		# Get active layer from TOC
		active_layer = iface.activeLayer()
		
		# test if a layer is selected
		if active_layer is None:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'No layer selected', level=Qgis.Critical)
			return
		
		# test if selected layer is a vector layer
		elif active_layer.type() != QgsMapLayerType.VectorLayer:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'The selected layer is not a VECTOR layer', level=Qgis.Critical)
			return
		
		# test if selected layer is a point feature layer
		elif active_layer.geometryType() != QgsWkbTypes.LineGeometry:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'The selected layer is not a LINE layer', level=Qgis.Critical)
			return
		
		# run function
		error, result = planning_lines_to_vertices(active_layer)
		
		# test success
		if error:
			iface.messageBar().pushMessage(u'Cruise Tools ', result, level=Qgis.Critical)
			return
		else:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'{}! Your Vertices file: {}'.format(return_success(),return_file_link(result)), level=Qgis.Success)
		
		# refresh canvas
		iface.mapCanvas().refresh()
		
		return
	
	def run_export_to_bridge(self):
		"""Export to Bridge"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
		# Get active layer from TOC
		active_layer = iface.activeLayer()
		
		# test if a layer is selected
		if active_layer is None:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'No layer selected', level=Qgis.Critical)
			return
		
		# test if selected layer is a vector layer
		elif active_layer.type() != QgsMapLayerType.VectorLayer:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'The selected layer is not a VECTOR layer', level=Qgis.Critical)
			return
		
		# if point then export_points, if line then export_lines
		if active_layer.geometryType() == QgsWkbTypes.PointGeometry:
			error, result = export_points_to_bridge(active_layer)
		elif active_layer.geometryType() == QgsWkbTypes.LineGeometry:
			error, result = export_lines_to_bridge(active_layer)
		# if something else, cancel
		else:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'The selected layer is not a POINT or LINE layer', level=Qgis.Critical)
			return
		
		# test success
		if error:
			iface.messageBar().pushMessage(u'Cruise Tools ', result, level=Qgis.Critical)
			return
		else:
			iface.messageBar().pushMessage(u'Cruise Tools ', u'{}! Your exported file: {}'.format(return_success(),return_file_link(result)), level=Qgis.Success)
		
		# refresh canvas
		iface.mapCanvas().refresh()
		
		return
	
	def run_settings(self):
		"""SETTINGS"""
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
			iface.messageBar().pushMessage(u'Cruise Tools ', u'{}! Saved settings successfully!'.format(return_success()), level=Qgis.Success)
		
		return
