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
                               fynn.warnke@yahoo.de
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
import math, processing
import qgis.utils

# Import Cruise Tools modules
from .write_point_coordinates import *
from .write_line_length import *
from .load_bathy import *
from .create_contours import *
from .swap_vectors import *

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
		
		icon = ':/plugins/cruisetools/images/icon.png'
		logo = self.add_action(icon,
									text=self.tr(u'Cruise Tools'),
									callback=self.run,
									parent=self.iface.mainWindow())
		
		icon = ':/plugins/cruisetools/images/write_point_coordinates.png'
		write_point_coordinates = self.add_action(icon,
									text=self.tr(u'Write Point Coordinates'),
									callback=self.run_wpc,
									parent=self.iface.mainWindow())
		
		icon = ':/plugins/cruisetools/images/write_line_length.png'
		write_line_length = self.add_action(icon,
									text=self.tr(u'Write Line Length'),
									callback=self.run_wll,
									parent=self.iface.mainWindow())
		
		icon = ':/plugins/cruisetools/images/load_bathy.png'
		load_bathy = self.add_action(icon,
									text=self.tr(u'Load Bathymetry Grid'),
									callback=self.run_lb,
									parent=self.iface.mainWindow())
		
		contour_menu = QMenu()
		
		cc_1000m = contour_menu.addAction(self.tr(u'1000 m'), self.run_cc_1000)
		cc_500m = contour_menu.addAction(self.tr(u'500 m'), self.run_cc_500)
		cc_100m = contour_menu.addAction(self.tr(u'100 m'), self.run_cc_100)
		cc_50m = contour_menu.addAction(self.tr(u'50 m'), self.run_cc_50)
		cc_10m = contour_menu.addAction(self.tr(u'10 m'), self.run_cc_10)
		cc_5m = contour_menu.addAction(self.tr(u'5 m'), self.run_cc_5)
		cc_1m = contour_menu.addAction(self.tr(u'1 m'), self.run_cc_1)
		
		icon = QIcon(':/plugins/cruisetools/images/create_contours.png')
		self.contourAction = QAction(icon, 'Create Contours', self.iface.mainWindow())
		self.contourAction.setMenu(contour_menu)
		
		self.contourButton = QToolButton()
		self.contourButton.setMenu(contour_menu)
		self.contourButton.setDefaultAction(self.contourAction)
#		self.contourButton.setPopupMode(QToolButton.MenuButtonPopup)
		self.contourButton.setPopupMode(QToolButton.InstantPopup)
		self.tranformToolbar = self.toolbar.addWidget(self.contourButton)

		
		icon = ':/plugins/cruisetools/images/swap_vectors.png'
		swap_vectors = self.add_action(icon,
									text=self.tr(u'Swap Vectors'),
									callback=self.run_sv,
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
		"""Fun Button"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"Awesome and practical Cruise Tools by the Bauernprogrammierers Fynn & Simon! <3", level=Qgis.Info)
		return

	def run_wpc(self):
		"""Write Point Coordinates"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
		# Get active layer from TOC
		active_layer = qgis.utils.iface.activeLayer()
		
		# test if a layer is selected
		if active_layer is None:
			qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"No layer selected", level=Qgis.Critical)
			return
		
		# test if selected layer is a vector layer
		elif active_layer.type() != QgsMapLayerType.VectorLayer:
			qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"The selected layer is not a VECTOR layer", level=Qgis.Critical)
			return
		
		# test if selected layer is a point feature layer
		elif active_layer.geometryType() != QgsWkbTypes.PointGeometry:
			qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"The selected layer is not a POINT layer", level=Qgis.Critical)
			return
		
		# Call the function
		write_point_coordinates(active_layer)
		
		# refresh canvas
		qgis.utils.iface.mapCanvas().refresh()
		
		# it's done
		qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"Hooray! Coordinates are in!", level=Qgis.Info)

	def run_wll(self):
		"""Write Line Length"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
		# Get active layer from TOC
		active_layer = qgis.utils.iface.activeLayer()
		
		# test if a layer is selected
		if active_layer is None:
			qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"No layer selected", level=Qgis.Critical)
			return
		
		# test if selected layer is a vector layer
		elif active_layer.type() != QgsMapLayerType.VectorLayer:
			qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"The selected layer is not a VECTOR layer", level=Qgis.Critical)
			return
		
		# test if selected layer is a line feature layer
		elif active_layer.geometryType() != QgsWkbTypes.LineGeometry:
			qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"The selected layer is not a LINE layer", level=Qgis.Critical)
			return
		
		# execute calculation & edit attribute table of active layer
		write_line_length(active_layer,True,True)
		
		# refresh canvas
		qgis.utils.iface.mapCanvas().refresh()
		
		# it's done
		qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"Hooray! Lengths are in!", level=Qgis.Info)

	def run_lb(self):
		"""Load Bathy"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
		# select grid file to be imported
		gridfile = select_bathy()
		
		# test if a file was selected
		if gridfile == '':
			qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"Load Bathymetry CANCELLED.", level=Qgis.Critical)
			return
		
		# load file twice with style def for color scale and hillshade
		grid_loaded = load_bathy(gridfile)
		
		# test if grid successfully loaded
		if not grid_loaded:
			qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"Something is wrong with that grid file.", level=Qgis.Critical)
			return
		
		# refresh canvas
		qgis.utils.iface.mapCanvas().refresh()
		
		# it's done
		qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"Hooray! Grid loaded successfully!\nRemember to adjust your COLOR SCALE and VERTICAL EXAGGERATION if necessary.", level=Qgis.Info)

	def run_cc_1000(self):
		self.run_cc(1000)

	def run_cc_500(self):
		self.run_cc(500)

	def run_cc_100(self):
		self.run_cc(100)

	def run_cc_50(self):
		self.run_cc(50)

	def run_cc_10(self):
		self.run_cc(10)

	def run_cc_5(self):
		self.run_cc(5)

	def run_cc_1(self):
		self.run_cc(1)

	def run_cc(self,interval):
		#Create Contours
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
		# Get active layer from TOC
		active_layer = qgis.utils.iface.activeLayer()
		
		# test if a layer is selected
		if active_layer is None:
			qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"No layer selected", level=Qgis.Critical)
			return
		
		# test if selected layer is a raster layer
		elif active_layer.type() != QgsMapLayerType.RasterLayer:
			qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"The selected layer is not a RASTER layer", level=Qgis.Critical)
			return
		
		# run function
		create_contours(active_layer,interval)
		
		# it's done
		qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"Hooray! Contours created successfully!", level=Qgis.Info)

	def run_sv(self):
		"""Swap Vectors"""
		if not self.pluginIsActive:
			self.pluginIsActive = True
		
		# Get active layer from TOC
		active_layer = qgis.utils.iface.activeLayer()
		
		# test if a layer is selected
		if active_layer is None:
			qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"No layer selected", level=Qgis.Critical)
			return
		
		# test if selected layer is a vector layer
		elif active_layer.type() != QgsMapLayerType.VectorLayer:
			qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"The selected layer is not a VECTOR layer", level=Qgis.Critical)
			return
		
		# test if selected layer is a line feature layer
		elif active_layer.geometryType() != QgsWkbTypes.LineGeometry:
			qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"The selected layer is not a line layer", level=Qgis.Critical)
			return
		
		# run function
		swap_vectors(active_layer)
		
		# refresh canvas
		qgis.utils.iface.mapCanvas().refresh()
		
		# it's done
		qgis.utils.iface.messageBar().pushMessage(u"Cruise Tools ", u"Hooray! Vectors swapped successfully!", level=Qgis.Info)
