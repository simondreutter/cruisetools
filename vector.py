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

# import some tools
from qgis.core import *
import math, processing

def dd2ddm(latitude, longitude):
	"""Convert decimal degree (DD) in degree and decimal minutes (DDM)"""
	# latitude
	if latitude > 0.:
		hemisphere = 'N'
	elif latitude == 0.:
		hemisphere = ''
	else:
		hemisphere = 'S'
	lat_d_, lat_degree = math.modf(abs(latitude))
	lat_dminute = lat_d_ * 60
	lat_DDM = u'{:02d}° {:06.3f}\' {}'.format(int(lat_degree), round(lat_dminute,3), hemisphere)
	
	# longitude
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

def write_point_coordinates(layer):
	"""Write the point coordinates (LAT/LONG) of the SHP file into the attribute table"""
	# get CRS of input layer and create coordinate transformation
	crs = layer.crs()
	#trans = QgsCoordinateTransform(crs, QgsCoordinateReferenceSystem('EPSG:4326'), QgsProject.instance())
	trans = QgsCoordinateTransform(crs, QgsProject.instance().crs(), QgsProject.instance())
	
	with edit(layer):
		# create fields for lat_DD and lon_DD coordinates in attribute table
		layer.addAttribute(QgsField("lat_DD",QVariant.Double,len=10,prec=6))
		layer.addAttribute(QgsField("lon_DD",QVariant.Double,len=10,prec=6))
		
		# create fields for lat_DDM and lon_DDM coordinates in attribute table
		layer.addAttribute(QgsField('lat_DDM',QVariant.String,len=10))
		layer.addAttribute(QgsField('lon_DDM',QVariant.String,len=10))
		
		# update attribute table fields
		layer.updateFields()
		
		# for all features in the layer
		for feature in layer.getFeatures():
			# get geometry of feature
			geom = feature.geometry().asPoint()
			
			# transform geometry to EPSG:4326 CRS
			geom4326 = trans.transform(geom)
			
			# set geometry of each feature in the vector layer into seperate fields
			feature.setAttribute(feature.fieldNameIndex('lat_DD'), geom4326.y())
			feature.setAttribute(feature.fieldNameIndex('lon_DD'), geom4326.x())
			
			# convert DD to DDM
			lat_ddm, lon_ddm = dd2ddm(geom4326.y(), geom4326.x())
			
			# set DDM geometry of each feature
			feature.setAttribute(feature.fieldNameIndex('lat_DDM'), lat_ddm)
			feature.setAttribute(feature.fieldNameIndex('lon_DDM'), lon_ddm)
			
			# ipdate attribute table
			layer.updateFeature(feature)
	
	return 0, None

def write_line_length(layer,m=True,nm=True):
	"""Write lengths of all features into attribute table"""
	# get CRS of input layer and create coordinate transformation
	crs = layer.crs()
	#trans = QgsCoordinateTransform(crs, QgsCoordinateReferenceSystem('EPSG:4326'), QgsProject.instance())
	trans = QgsCoordinateTransform(crs, QgsProject.instance().crs(), QgsProject.instance())
	
	# set project ellipsoid (for measurements) to CRS ellipsoid
	ellipsoid = QgsProject.instance().crs().ellipsoidAcronym()
	QgsProject.instance().setEllipsoid(ellipsoid)

	# Initialize Distance calculator class with project ellipsoid
	l = QgsDistanceArea()
	l.setEllipsoid(ellipsoid)
	
	with edit(layer):
		# create fields for length_m and/or length_nm
		if m:
			layer.addAttribute(QgsField('length_m',QVariant.Double,len=15,prec=5))
		if nm:
			layer.addAttribute(QgsField('length_nm',QVariant.Double,len=15,prec=5))
		
		# update attribute table fields
		layer.updateFields()
		
		# for all features in the layer
		for feature in layer.getFeatures():
			# get geometry of feature
			geom = feature.geometry()
			
			# transform geometry to EPSG:4326
			geom.transform(trans)
			
			# measure feature length in meters
			len_m  = l.measureLength(geom)
			
			if nm:
				# convert m to nm
				len_nm = l.convertLengthMeasurement(len_m, QgsUnitTypes.DistanceNauticalMiles)
			
			# set field values according to the calculated length
			if m:
				feature.setAttribute(layer.fields().indexFromName('length_m'), len_m)
			if nm:
				feature.setAttribute(layer.fields().indexFromName('length_nm'), len_nm)			
			
			# update attribute table
			layer.updateFeature(feature)
	
	return 0, None

def write_polygon_area(layer,m2=True,km2=True):
	"""Write area of all polygon features into attribute table"""
	# get CRS of input layer and create coordinate transformation
	crs = layer.crs()
	#trans = QgsCoordinateTransform(crs, QgsCoordinateReferenceSystem('EPSG:4326'), QgsProject.instance())
	trans = QgsCoordinateTransform(crs, QgsProject.instance().crs(), QgsProject.instance())

	# set project ellipsoid (for measurements) to CRS ellipsoid
	ellipsoid = QgsProject.instance().crs().ellipsoidAcronym()
	QgsProject.instance().setEllipsoid(ellipsoid)

	# Initialize Distance calculator class with project ellipsoid
	l = QgsDistanceArea()
	l.setEllipsoid(ellipsoid)
	
	with edit(layer):
		# create attribute table fields for specified units
		if m2:
			layer.addAttribute(QgsField('area_m2',QVariant.Double,len=15,prec=5))
		if km2:
			layer.addAttribute(QgsField('area_km2',QVariant.Double,len=15,prec=5))
			
		layer.updateFields()
		
		# for all features in polygon layer
		for feature in layer.getFeatures():
			# get geometry
			geom = feature.geometry()
			
			# transform geometry to EPSG:4236
			geom.transform(trans)
			
			# area in SQUARE METERS
			area_m2 = l.measureArea(geom)
			
			# area in SQUARE KILOMETERS
			if km2:
				area_km2 = l.convertAreaMeasurement(area_m2, QgsUnitTypes.AreaSquareKilometers)
			
			# set field values according to calculated AREA
			if m2:
				feature.setAttribute(layer.fields().indexFromName('area_m2'), area_m2)
			if km2:
				feature.setAttribute(layer.fields().indexFromName('area_km2'), area_km2)
			
			# update attribute table
			layer.updateFeature(feature)
	
	return 0, None

def swap_vectors(layer):
	"""Swap line vector direction"""
	with edit(layer):
		# reverse line direction for each feature 
		for feature in layer.getFeatures():
			geom = feature.geometry()
			if geom.isMultipart():
				mls = QgsMultiLineString()
				for line in geom.asGeometryCollection():
					mls.addGeometry(line.constGet().reversed())
					newgeom = QgsGeometry(mls)
				layer.changeGeometry(feature.id(),newgeom)
			else:
				newgeom = QgsGeometry(geom.constGet().reversed())
				layer.changeGeometry(feature.id(),newgeom)
	
	return 0, None
