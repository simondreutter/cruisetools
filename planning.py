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
import os
import processing

# import Cruise Tools modules
from .auxiliary_tools import *
from .config import *
from .vector import *

style_planning_lines = ':/plugins/cruisetools/styles/style_planning_lines.qml'
style_planning_points = ':/plugins/cruisetools/styles/style_planning_points.qml'
style_planning_lines_vertices = ':/plugins/cruisetools/styles/style_planning_lines_vertices.qml'

def create_point_planning_file():
	"""Create point planning file"""
	# set output file
	title = 'Create Point Planning File'
	path = os.path.join(QgsProject.instance().homePath(),'point_planning')
	filter = 'GeoPackage (*.gpkg);;ESRI Shapefile (*.shp)'
	output = select_ouput_file(title,path,filter)
	base_path,base_name,ext = get_info_from_path(output)
	
	# test if a file was selected
	if output == '':
		return 1, 'No file selected!'
	
	# get output file driver (GPKG or ESRI Shapefile)
	driver = get_driver_from_path(output)
	
	# test if a driver could be identified
	if driver is None:
		return 1, 'File driver could not be identified!'
	
	# create temporary memory vector layer
	uri = 'Point?crs=epsg:4326&field=name:string(50)&field=notes:string(0)&index=yes'
	tmp_layer = QgsVectorLayer(uri, base_name, 'memory')
	
	# write empty layer to file
	error, result = QgsVectorFileWriter.writeAsVectorFormat(tmp_layer, output, 'utf-8', driverName=driver)
	if error != QgsVectorFileWriter.NoError:
		return 1, 'File could not be written!'
	
	# dereference tmp_layer
	tmp_layer = None
	
	# load points from file
	planning_layer = QgsVectorLayer(output, base_name, 'ogr')
	
	# load planning style from style file
	planning_layer.loadNamedStyle(style_planning_points)
	
	# add to canvas
	QgsProject.instance().addMapLayer(planning_layer)
	
	return 0, output

def create_line_planning_file():
	"""Create line planning file"""
	# set output file
	title = 'Create Line Planning File'
	path = os.path.join(QgsProject.instance().homePath(),'line_planning')
	filter = 'GeoPackage (*.gpkg);;ESRI Shapefile (*.shp)'
	output = select_ouput_file(title,path,filter)
	base_path,base_name,ext = get_info_from_path(output)
	
	# test if a file was selected
	if output == '':
		return 1, 'No file selected!'
	
	# get output file driver (GPKG or ESRI Shapefile)
	driver = get_driver_from_path(output)
	
	# test if a driver could be identified
	if driver is None:
		return 1, 'File driver could not be identified!'
	
	# create temporary memory vector layer
	uri = 'Linestring?crs=epsg:4326&field=name:string(50)&field=turnRadius_nm:double(4,2)&field=maxSpeed_kn:double(4,2)&field=notes:string(0)&index=yes'
	tmp_layer = QgsVectorLayer(uri, base_name, 'memory')
	
	# write empty layer to file
	error, result = QgsVectorFileWriter.writeAsVectorFormat(tmp_layer, output, 'utf-8', driverName=driver)
	if error != QgsVectorFileWriter.NoError:
		return 1, 'File could not be written!'
	
	# dereference tmp_layer
	tmp_layer = None
	
	# load lines from file
	planning_layer = QgsVectorLayer(output, base_name, 'ogr')
	
	# load planning style from style file
	planning_layer.loadNamedStyle(style_planning_lines)
	
	# add to canvas
	QgsProject.instance().addMapLayer(planning_layer)
	
	return 0, output

def planning_lines_to_vertices(line_layer):
	"""Convert planning line files to vertices for coordinate export"""
	# set output file
	name = line_layer.name()
	title = 'Create Vertices From Lines'
	path = os.path.join(QgsProject.instance().homePath(),'{}_vertices'.format(name))
	filter = 'GeoPackage (*.gpkg);;ESRI Shapefile (*.shp)'
	output = select_ouput_file(title,path,filter)
	base_path,base_name,ext = get_info_from_path(output)
	
	# test if a file was selected
	if output == '':
		return 1, 'No file selected!'
	
	# get output file driver (GPKG or ESRI Shapefile)
	driver = get_driver_from_path(output)
	
	# test if a driver could be identified
	if driver is None:
		return 1, 'File driver could not be identified!'
	
	tmp_layer = lines_to_vertices(line_layer,base_name)
	
	# write memory layer to disk
	error, result = QgsVectorFileWriter.writeAsVectorFormat(tmp_layer, output, 'utf-8', driverName=driver)
	if error != QgsVectorFileWriter.NoError:
		return 1, 'File could not be written!'
	
	# dereference tmp_layer
	tmp_layer = None
	
	# load lines from file
	vertex_layer = QgsVectorLayer(output, base_name, 'ogr')
	
	# add corrdinates to attributes
	write_point_coordinates(vertex_layer)
	
	# load planning style from style file
	vertex_layer.loadNamedStyle(style_planning_lines_vertices)
	
	# add to canvas
	QgsProject.instance().addMapLayer(vertex_layer)
	
	return 0, output

def lines_to_vertices(line_layer,name):
	"""Convert lines to vertices (helper function)"""
	# create temporary memory vector layer
	vertex_layer = QgsVectorLayer('Point?crs=epsg:4326', name, 'memory')
	provider = vertex_layer.dataProvider()
	
	# initialize attribute fields
	provider.addAttributes(line_layer.fields())
	provider.deleteAttributes([0])
	vertex_layer.updateFields()
	
	# check if any features are selected and only use those in that case
	if line_layer.selectedFeatureCount() == 0:
		input_features = line_layer.getFeatures()
	elif line_layer.selectedFeatureCount() > 0:
		input_features = line_layer.getSelectedFeatures()
	
	with edit(vertex_layer):
		# get geometry and attributes of all line features
		for vertice in input_features:
			# initialize feature
			feature = QgsFeature(vertex_layer.fields())
			
			# get line attributes
			attrs = vertice.attributes()
			
			# write copied attributes
			for i, attrField in enumerate(line_layer.fields().names()[1:]):
				feature.setAttribute(attrField, attrs[i+1])
			
			# get line geometry (start and end points)
			geom = vertice.geometry().asPolyline()
			start_point = geom[0]
			end_point = geom[-1]
			
			for g in geom:
				feature.setGeometry(QgsGeometry.fromPointXY(g))
				provider.addFeatures([feature])
			
			vertex_layer.updateFeature(feature)
			vertex_layer.updateFields()
	
	return vertex_layer

def export_points_to_bridge(point_layer):
	"""Export planning points for vessel ECDIS transfer"""
	# get vesser from config
	vessel = get_vessel_config()
	
	# get CRS of input layer and create coordinate transformation
	crs = point_layer.crs()
	trans = QgsCoordinateTransform(crs, QgsCoordinateReferenceSystem('EPSG:4326'), QgsProject.instance())
	
	# check if any features are selected and only use those in that case
	if point_layer.selectedFeatureCount() == 0:
		input_features = point_layer.getFeatures()
	elif point_layer.selectedFeatureCount() > 0:
		input_features = point_layer.getSelectedFeatures()
	
	# empty list for features
	table =[]
	
	# create dict holding all features with fieldnames and geometry
	for i,feature in enumerate(input_features):
		feature_fields = feature.fields().names()
		feature_attributes = feature.attributes()
		# add minimum of required fields if they don't exist
		if not 'fid' in feature_fields:
			feature_fields.append('fid')
			feature_attributes.append(i+1)
		if not 'name' in feature_fields:
			feature_fields.append('name')
			feature_attributes.append('')
		# zip lists to dict
		feature_dict = dict(zip(feature_fields,feature_attributes))
		# get geometry of feature
		geom = feature.geometry().asPoint()
		# transform geometry to EPSG:4326 CRS
		geom4326 = trans.transform(geom)
		feature_dict['lat_DD'] = geom4326.y()
		feature_dict['lon_DD'] = geom4326.x()
		# convert DD to DDM
		lat_ddm, lon_ddm = dd2ddm(geom4326.y(), geom4326.x())
		feature_dict['lat_DDM'] = lat_ddm
		feature_dict['lon_DDM'] = lon_ddm
		
		table.append(feature_dict)
	
	# select export function from vessel
	if vessel == 'default':
		error, result = export_csv(table,point_layer.name())
	elif vessel == 'RV Sonne':
		error, result = export_SAM_route(table,vessel,point_layer.name())
	elif vessel == 'RV Maria S. Merian':
		error, result = export_SAM_route(table,vessel,point_layer.name())
	elif vessel == 'RV Polarstern':
		error, result = export_csv(table,point_layer.name())
	
	return error, result

def export_lines_to_bridge(line_layer):
	"""Export planning lines for vessel ECDIS transfer"""
	# get layer with line vertices
	vertex_layer = lines_to_vertices(line_layer,line_layer.name())
	
	# export points
	error, result = export_points_to_bridge(vertex_layer)
	
	# dereference vertex_layer
	vertex_layer = None
	
	return error, result

def export_csv(table,name):
	"""Export table as Comma Separated Value [CSV]"""
	# set output file
	title = 'Export Points to CSV'
	path = os.path.join(QgsProject.instance().homePath(),name)
	filter = 'Comma Separated Value [CSV] (*.csv)'
	output = select_ouput_file(title,path,filter)
	base_path,base_name,ext = get_info_from_path(output)
	
	# test if a file was selected
	if output == '':
		return 1, 'No file selected!'
	
	# header line
	key_list = ['"' + x + '"' for x in table[0].keys()]
	#header = ','.join(table[0].keys())
	header = ','.join(key_list)
	
	# write table to file
	with open(output, 'w',encoding='ansi') as f:
		# write header
		f.write(header + '\n')
		# write fields and geometry from features
		for feature in table:
			line = []
			for field in header.split(','):
				line.append(feature[field.replace('"','')])
			line = ['"' + str(x).replace('NULL','') + '"' for x in line]
			f.write(','.join(line) + '\n')
	
	return 0, output

def export_SAM_route(table,vessel,name):
	"""Export table as SAM Route to bridge Comma Separated Value [CSV]"""
	# set output file
	title = 'Export Points to SAM Route'
	path = os.path.join(QgsProject.instance().homePath(),name)
	filter = 'Comma Separated Value [CSV] (*.csv)'
	output = select_ouput_file(title,path,filter)
	base_path,base_name,ext = get_info_from_path(output)
	
	# test if a file was selected
	if output == '':
		return 1, 'No file selected!'
		
	with open(output,'w',encoding='ansi') as f:
		f.write('"Name","Latitude [°]","Longitude [°]","Turn Radius [NM]","Max. Speed [kn]","XTD [m]","Sailmode","Additional Notes"\n')
		for feature in table:
			# concat name and fid for 'Name' column
			if feature['name'] == '':
				name_out = feature['fid']
			else:
				name_out = str(feature['fid']) + '_' + feature['name']
			for i in ['turnRadius_nm','maxSpeed_kn','notes']:
				if not i in feature:
					feature[i] = ''
			# compose line
			line = '"{}","{}","{}","{}","{}","","","{}"\n'.format(name_out,
													round(feature['lat_DD'],6),
													round(feature['lon_DD'],6),
													feature['turnRadius_nm'],
													feature['maxSpeed_kn'],
													feature['notes'])
			# replace empty fields ('NULL') with nothing ('')
			line = line.replace('NULL','')
			# write line to file
			f.write(line)
	
	return 0, output
