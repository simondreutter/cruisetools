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

# import some tools
from qgis.core import *
import os
import random

# make new directory
def mkdir(directory):
	"""Create a new folder if it doesn't exist already"""
	if not os.path.isdir(directory):
		os.makedirs(directory)
	
	return directory

def select_ouput_file(title,path,filter):
	"""Select output file"""
	if title == None:
		title = 'Export'
	if path == None:
		path = QgsProject.instance().homePath()
	dialog = QFileDialog()
	f, _filter = QFileDialog.getSaveFileName(dialog, title, path, filter)
	
	return f

def select_input_file(title,path,filter):
	"""Select input file"""
	if title == None:
		title = 'Import'
	if path == None:
		path = QgsProject.instance().homePath()
	dialog = QFileDialog()
	f, _filter = QFileDialog.getOpenFileName(dialog, title, path, filter)
	
	return f

def get_driver_from_path(file_path):
	"""Get GDAL driver from file path"""
	ext = os.path.splitext(file_path)[1].upper()
	if '.TIF' in ext:
		return 'GTiff'
	elif ext == '.GPKG':
		return 'GPKG'
	elif ext == '.SHP':
		return 'ESRI Shapefile'
	elif ext == '.XLSX':
		return 'xlsx'
	
	return None

def get_info_from_path(file_path):
	"""Get file info from file path"""
	file_info = QFileInfo(file_path)
	# base path to create contours directory
	base_path = file_info.absolutePath()
	# base name for output
	base_name = file_info.baseName()
	# extension
	ext = os.path.splitext(file_path)[1]
	
	return base_path,base_name,ext

def return_file_link(path):
	"""Return link to file for messageBar"""
	# TODO: find a way to make the file link actually clickable!
	return '<a href="{0}">{0}</a>'.format(path)

def return_success():
	"""Return success message"""
	success_messages = ['Aye',
						'Boom',
						'Cool',
						'Çüş',
						'Habibi',
						'Heureka',
						'Hooray',
						'Hot AF',
						'I bims',
						'Ja Moin',
						'Laser',
						'Lurch',
						'Nice',
						'Noise',
						'Rasiert',
						'Score',
						'Sweet',
						'Tschackalacka',
						'Turbo',
						'Whoop',
						'Yeah',
						'Yiihaa']
	success_message = random.choice(success_messages)
	
	return success_message
