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

# Import some tools
from qgis.core import *
import qgis.utils

# Style files for layers
style_bathy = ':/plugins/cruisetools/styles/style_bathy.qml'
style_hillshade_prj = ':/plugins/cruisetools/styles/style_hillshade_prj.qml'
style_hillshade_geo = ':/plugins/cruisetools/styles/style_hillshade_geo.qml'

def select_bathy():
	""" Select Grid file to load. """
	# Open dialog box to select *.tif or other supported grid
	title = 'Select a Bathymetry Grid'
	dialog = QFileDialog()
	path = QgsProject.instance().homePath()
	filter = "tif (*.tif *.tiff);;netCDF (*.nc *.grd)"
	f, _filter = QFileDialog.getOpenFileName(dialog, title, path, filter)
	return f

def load_bathy(f):
	""" Load grid file with color palette and hillshade. """
	# Get base name of input file
	fileInfo = QFileInfo(f)
	base_name = fileInfo.baseName()
	
	# BATHY:
	# Load grid with layer style file style_bathy.qml
	layer_bathy = QgsRasterLayer(f, base_name)
	
	# Test if the files loads properly
	if not layer_bathy.isValid():
		return False
	
	# Create group with layer base_name
	root = QgsProject.instance().layerTreeRoot()
	bathy_group = root.addGroup(base_name)
	
	bathy_group.insertChildNode(1, QgsLayerTreeLayer(layer_bathy))
	layer_bathy.loadNamedStyle(style_bathy)
	layer_bathy.triggerRepaint()
	QgsProject.instance().addMapLayer(layer_bathy, False)
	
	# HILLSHADE:
	# Load grid again with layer style file style_hillshade.qml
	layer_hillshade = QgsRasterLayer(f, base_name + '_hillshade')
	QgsProject.instance().addMapLayer(layer_hillshade, False)
	bathy_group.insertChildNode(0, QgsLayerTreeLayer(layer_hillshade))
	
	# If raster is geographic, load hillshade_geo style (different exaggeration)
	if layer_bathy.crs().authid() == 'EPSG:4326':
		layer_hillshade.loadNamedStyle(style_hillshade_geo)
	# else load hillste_prj style
	else:
		layer_hillshade.loadNamedStyle(style_hillshade_prj)
	layer_hillshade.triggerRepaint()
	
	return True
