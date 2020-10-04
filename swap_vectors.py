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

def swap_vectors(wrk_layer):
	""" Swap line vector direction. """
	with edit(wrk_layer):
		# Reverse line direction for each feature 
		for feature in wrk_layer.getFeatures():
			geom = feature.geometry()
			if geom.isMultipart():
				mls = QgsMultiLineString()
				for line in geom.asGeometryCollection():
					mls.addGeometry(line.constGet().reversed())
					newgeom = QgsGeometry(mls)
				wrk_layer.changeGeometry(feature.id(),newgeom)
			else:
				newgeom = QgsGeometry(geom.constGet().reversed())
				wrk_layer.changeGeometry(feature.id(),newgeom)
