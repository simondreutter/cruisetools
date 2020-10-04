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

# Import some tools
from qgis.core import *
import os, processing

# Import Cruise Tools modules
from .write_line_length import *
from .swap_vectors import *

#interval = 100
style_contours = ':/plugins/cruisetools/styles/style_contours.qml'

def mkdir(directory):
	""" Create a new folder if it doesn't exist already. """
	if not os.path.isdir(directory):
		os.makedirs(directory)

def create_contours(raster,interval):
	""" Create contour lines from input raster. """
	fileInfo = QFileInfo(raster.source())
	# Base path to create contours directory
	base_path = fileInfo.absolutePath()
	# Base name for output
	base_name = fileInfo.baseName()
	# Set contourname
	contourname = base_name + '_contour_' + str(interval) + 'm'
	# Set directory in which to create contours
	contour_path = base_path + '/contours'
	# Compile contour name from original filename plus suffix containing contour interval
	out_path = contour_path + '/' + contourname + '.gpkg'
	# Create output directory
	mkdir(contour_path)
	
	# Get CRS from raster file (for some reasons gdal:contour is assigning a false CRS otherwise...)
	crs = raster.crs()
	
	# Parameters for contour algortihm
	params_contour = {'INPUT': raster,
						'BAND': 1,
						'INTERVAL': interval,
						'FIELD_NAME': 'ELEV',
						'CREATE_3D': False,
						'IGNORE_NODATA': False,
						'NODATA': raster.dataProvider().sourceNoDataValue(1), # 1 -> band number
						'OFFSET': 0,
						'OUTPUT':'memory:*.gpkg'}
	contours_tmp = processing.run('gdal:contour', params_contour)
	
	# Parameters for smoothing
	params_smooth = {'INPUT': contours_tmp['OUTPUT'],
						'ITERATIONS' : 3,
						'MAX_ANGLE' : 180,
						'OFFSET' : 0.25,
						'OUTPUT': out_path}
	contours_smooth = processing.run('native:smoothgeometry', params_smooth)
	
	# Load contours from file
	#contours = list(contours_smooth.values())[0]
	contours = contours_smooth['OUTPUT']
	contours_lyr = QgsVectorLayer(contours, contourname, 'ogr')
	
	# Set original CRS
	contours_lyr.setCrs(crs)
	
	# Add to canvas
	QgsProject.instance().addMapLayers([contours_lyr])
	
	# Write line lengths to table in order to filter short lines
	write_line_length(contours_lyr,True,False)
	
	# Bathy grids are often Z +down so the vectors need to be swapped
	swap_vectors(contours_lyr)
	
	# Load contour style from style file
	contours_lyr.loadNamedStyle(style_contours)
