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
import math, processing

def dd2ddm(latitude, longitude):
	""" Convert decimal degree (DD) in degree and decimal minutes (DDM) """
	# Latitude
	if latitude > 0.:
		hemisphere = 'N'
	elif latitude == 0.:
		hemisphere = ''
	else:
		hemisphere = 'S'
	lat_d_, lat_degree = math.modf(abs(latitude))
	lat_dminute = lat_d_ * 60
	lat_DDM = '{:02d}° {:06.3f}\' {}'.format(int(lat_degree), round(lat_dminute,3), hemisphere)
	
	# Longitude
	if longitude > 0.:
		hemisphere = 'E'
	elif longitude == 0.:
		hemisphere = ''
	else:
		hemisphere = 'W'
	lon_d_, lon_degree = math.modf(abs(longitude))
	lon_dminute = lon_d_ * 60
	lon_DDM = u'{:03d}° {:06.3f}\' {}'.format(int(lon_degree), round(lon_dminute,3), hemisphere)
	
	return lat_DDM, lon_DDM

def write_point_coordinates(wrk_layer):
	""" Write the point coordinates (LAT/LONG) of the SHP file into the attribute table. """
	# Get CRS of input layer and create coordinate transformation
	crs = wrk_layer.crs()
	trans = QgsCoordinateTransform(crs, QgsCoordinateReferenceSystem('EPSG:4326'), QgsProject.instance())
	
	with edit(wrk_layer):
		# Create fields for lat_DD and lon_DD coordinates in attribute table
		wrk_layer.addAttribute(QgsField("lat_DD",QVariant.Double,len=10,prec=6))
		wrk_layer.addAttribute(QgsField("lon_DD",QVariant.Double,len=10,prec=6))
		
		# Create fields for lat_DDM and lon_DDM coordinates in attribute table
		wrk_layer.addAttribute(QgsField('lat_DDM',QVariant.String,len=10))
		wrk_layer.addAttribute(QgsField('lon_DDM',QVariant.String,len=10))
		
		# Update attribute table fields
		wrk_layer.updateFields()
		
		# For all features in the wrk_layer
		for feature in wrk_layer.getFeatures():
			# Get geometry of feature
			geom = feature.geometry().asPoint()
			
			# Transform geometry to EPSG:4326 CRS
			geom4326 = trans.transform(geom)
			
			# Set geometry of each feature in the vector layer into seperate fields
			feature.setAttribute(feature.fieldNameIndex('lat_DD'), geom4326.y())
			feature.setAttribute(feature.fieldNameIndex('lon_DD'), geom4326.x())
			
			# Convert DD to DDM
			lat_ddm, lon_ddm = dd2ddm(geom4326.y(), geom4326.x())
			
			# Set DDM geometry of each feature
			feature.setAttribute(feature.fieldNameIndex('lat_DDM'), lat_ddm)
			feature.setAttribute(feature.fieldNameIndex('lon_DDM'), lon_ddm)
			
			# Update attribute table
			wrk_layer.updateFeature(feature)
