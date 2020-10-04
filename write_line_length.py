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

# Initialize Distance calculator class
l = QgsDistanceArea()
l.setEllipsoid('WGS84')

def write_line_length(wrk_layer,m,nm):
	""" Write lengths of all features into attribute table """
	# Get CRS of input layer and create coordinate transformation
	crs = wrk_layer.crs()
	trans = QgsCoordinateTransform(crs, QgsCoordinateReferenceSystem('EPSG:4326'), QgsProject.instance())
	
	with edit(wrk_layer):
		# Create fields for length_m and/or length_nm
		if m:
			wrk_layer.addAttribute(QgsField('length_m',QVariant.Double,len=15,prec=5))
		if nm:
			wrk_layer.addAttribute(QgsField('length_nm',QVariant.Double,len=15,prec=5))
		
		# Update attribute table fields
		wrk_layer.updateFields()
		
		# For all features in the wrk_layer
		for feature in wrk_layer.getFeatures():
			# Get geometry of feature
			geom = feature.geometry()
			
			# Transform geometry to EPSG:4326
			geom.transform(trans)
			
			# Measure feature length in meters
			len_m  = l.measureLength(geom)
			
			if nm:
				# Convert m to nm
				len_nm = l.convertLengthMeasurement(len_m, QgsUnitTypes.DistanceNauticalMiles)
			
			# Set field values according to the calculated length
			if m:
				feature.setAttribute(wrk_layer.fields().indexFromName('length_m'), len_m)
			if nm:
				feature.setAttribute(wrk_layer.fields().indexFromName('length_nm'), len_nm)			
			
			# Update attribute table
			wrk_layer.updateFeature(feature)
