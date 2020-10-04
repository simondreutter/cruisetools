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
from qgis.utils import *
import processing
import os
import gdal
import gdalconst
import numpy as np

# import Cruise Tools modules
from .auxiliary_tools import *
from .config import *

# raster export options
extension = '.tif'
# set vertical exaggeration
z_factor = 5.0

# style files for layers
style_hillshade_prj = ':/plugins/cruisetools/styles/style_hillshade_prj.qml'
style_hillshade_geo = ':/plugins/cruisetools/styles/style_hillshade_geo.qml'

def load_bathy():
	"""Load grid file with color palette and hillshade"""
	# select grid file to be imported
	title = 'Select a Bathymetry Grid'
	path = QgsProject.instance().homePath()
	filter = 'GTiff (*.tif *.tiff);;netCDF (*.nc *.grd)'
	gridfile = select_input_file(title,path,filter)
	
	# test if a file was selected
	if gridfile == '':
		return 1,'No grid file selected!'
	
	# read colors and min max values from settings.ini
	colors = get_colors_config()
	min,max = get_minmax_config()
	min = int(min)
	max = int(max)
	
	# get file info
	base_path,base_name,ext = get_info_from_path(gridfile)
	
	# BATHY:
	# load grid
	layer_bathy = QgsRasterLayer(gridfile, base_name)
	
	# test if the files loads properly
	if not layer_bathy.isValid():
		return 1,'Could not load selected file!'
	
	# create color scale values
	n_values = len(colors)
	width = max - min
	step = width / (n_values - 1)
	values = []
	value = min
	for i in range(n_values):
		values.append(value)
		value = value + step
	
	# create color ramp
	ramp = []
	for i, item in enumerate(colors):
		ramp.append(QgsColorRampShader.ColorRampItem(values[i],QColor(str(item)),str(values[i])))
	color_ramp = QgsColorRampShader()
	color_ramp.setColorRampItemList(ramp)
	color_ramp.setColorRampType(QgsColorRampShader.Interpolated)
	
	# create shader and set color ramp
	shader = QgsRasterShader()
	shader.setRasterShaderFunction(color_ramp)
	
	# create renderer
	renderer = QgsSingleBandPseudoColorRenderer(layer_bathy.dataProvider(),layer_bathy.type(),shader)
	
	# set min max values
	renderer.setClassificationMin(min)
	renderer.setClassificationMax(max)
	
	# apply renderer to layer
	layer_bathy.setRenderer(renderer)
	
	# apply brightness & contrast of layer
	brightness_filter = QgsBrightnessContrastFilter()
	brightness_filter.setBrightness(-20)
	brightness_filter.setContrast(10)
	layer_bathy.pipe().set(brightness_filter)
	
	# apply resample filter (Bilinear)
	resample_filter = layer_bathy.resampleFilter()
	resample_filter.setZoomedInResampler(QgsBilinearRasterResampler())
	resample_filter.setZoomedOutResampler(QgsBilinearRasterResampler())
	
	# create group with layer base_name
	root = QgsProject.instance().layerTreeRoot()
	bathy_group = root.addGroup(base_name)
	
	# add bathy layer to group
	bathy_group.insertChildNode(1, QgsLayerTreeLayer(layer_bathy))
	
	# add bathy layer to project
	layer_bathy.triggerRepaint()
	QgsProject.instance().addMapLayer(layer_bathy, False)
	
	# HILLSHADE:
	# load grid again with layer style file style_hillshade.qml
	layer_hillshade = QgsRasterLayer(gridfile, base_name + '_hillshade')
	
	# if raster is geographic, load hillshade_geo style (different exaggeration)
	if layer_bathy.crs().isGeographic():
		layer_hillshade.loadNamedStyle(style_hillshade_geo)
	# else load hillste_prj style
	else:
		layer_hillshade.loadNamedStyle(style_hillshade_prj)
	
	# add hillshade layer to group
	bathy_group.insertChildNode(0, QgsLayerTreeLayer(layer_hillshade))
	
	# add hillshade layer to project
	layer_hillshade.triggerRepaint()
	QgsProject.instance().addMapLayer(layer_hillshade, False)
	
	return 0,None

def get_out(base_path,name,extension):
	"""Get output file's path from base name and path plus suffix and extension"""
	path = os.path.join(base_path, name + extension)
	return path

def create_rgb(layer,output):
	"""Render and write RGB file"""
	# get layer properties
	extent = layer.extent()
	width, height = layer.width(), layer.height()
	renderer = layer.renderer()
	provider = layer.dataProvider()
	crs = layer.crs()
	
	# create pipe for export
	pipe = QgsRasterPipe()
	pipe.set(provider.clone())
	pipe.set(renderer.clone())
	
	# create FileWriter and write file
	fwriter = QgsRasterFileWriter(output)
	error = fwriter.writeRaster(pipe,width,height,extent,crs)
	if error != fwriter.NoError:
		return 1, 'RGB file could not be rendered!'
	
	return 0, output

"""
def create_rgb(layer,out_path):
	#Get auxiliary variables like path and file writer and render RGB
	# get layer info
	base_path,base_name,ext = get_info_from_path(layer.source())

	# new name and path
	rgb_file = get_out(out_path,'tmp_RGB',extension)
		
	# get layer properties
	extent = layer.extent()
	width, height = layer.width(), layer.height()
	renderer = layer.renderer()
	provider = layer.dataProvider()
	crs = layer.crs()
	
	# create pipe for export
	pipe = QgsRasterPipe()
	pipe.set(provider.clone())
	pipe.set(renderer.clone())
	
	# create FileWriter and write file
	fwriter = QgsRasterFileWriter(rgb_file)
	error = fwriter.writeRaster(pipe,width,height,extent,crs)
	if error != fwriter.NoError:
		return None,None,None,None
	
	return base_path,base_name,rgb_file,crs
"""

def get_scale(crs):
	"""Get scale for vertical units in grid"""
	# if the grid is geographic, vertical will be interpreted as degree
	# hence the scale needs to be 0.000009.
	if crs.isGeographic():
		scale = 0.000009
	# otherwise it's considered in meters and the scale is 1.
	else:
		scale = 1.0
	return scale

def create_hs(input,scale,output,compress):
	"""Create hillshade grid from raster input"""
	hs_params = {'INPUT': input,
				'BAND': 1,
				'Z_FACTOR': z_factor*scale,
				'SCALE': 1.0,
				'AZIMUTH': 315.0,
				'ALTITUDE': 45.0,
				'COMPUTE_EDGES': True,
				'MULTIDIRECTIONAL': False,
				'OPTIONS': 'COMPRESS={}'.format(compress),
				'OUTPUT': output}
	processing.run('gdal:hillshade', hs_params)
	return output

def create_slope(input,scale,output,compress):
	"""Create slope grid from raster input"""
	slope_params = {'INPUT': input,
					'Z_FACTOR': scale,
					'OPTIONS': 'COMPRESS={}'.format(compress),
					'OUTPUT': output}
	processing.run('qgis:slope', slope_params)
	return output

def stretch_min_max(input,output,compress):
	"""Stretch grey scale image to min max"""
	dmin = 1.
	dmax = 254.
	layer = QgsRasterLayer(input, 'tmp', 'gdal')
	extent = layer.extent()
	provider = layer.dataProvider()
	stats = provider.bandStatistics(1, QgsRasterBandStats.All, extent, 0)
	smin = stats.minimumValue
	smax = stats.maximumValue
	translate_params = {'INPUT': input,
						'NO_DATA': 0,
						'RTYPE': 0,
						'OPTIONS': 'COMPRESS={}'.format(compress),
						'EXTRA': '-scale {} {} {} {}'.format(smin,smax,dmin,dmax),
						'OUTPUT': output}
	processing.run('gdal:translate', translate_params)
	layer = None
	return output

def create_inv(input,output,compress):
	"""Create inverted slope grid"""
	calc_params = {'INPUT_A': input,
					'BAND_A': 1,
					'FORMULA': 'uint8(255. - A)',
					'NO_DATA': 0,
					'RTYPE': 0,
					'OPTIONS': 'COMPRESS={}'.format(compress),
					'EXTRA': '--overwrite',
					'OUTPUT': output}
	processing.run('gdal:rastercalculator', calc_params)
	return output

def shade(rgb,b,c,syntax,temp_folder,output,compress):
	"""Create shaded RGB grid from plain color grid and up to two additional shading grids"""
	tmp_file = get_out(temp_folder,'tmp_SHADE',extension)
	calc_params = {'INPUT_A': rgb,
					'BAND_A': 1,
					'INPUT_B': b,
					'BAND_B': 1,
					'INPUT_C': c,
					'BAND_C': 1,
					'FORMULA': syntax,
					'NO_DATA': 0,
					'RTYPE': 0,
					'OPTIONS': 'COMPRESS={}'.format(compress),
					'EXTRA': '--allBands=A --overwrite',
					'OUTPUT': tmp_file}
	processing.run('gdal:rastercalculator', calc_params)
	translate_params = {'INPUT': tmp_file,
						'NO_DATA': 0,
						'RTYPE': 0,
						'OPTIONS': 'COMPRESS={}'.format(compress),
						'EXTRA': '-b 1 -b 2 -b 3 -r bilinear -a_nodata "0 0 0"',
						'OUTPUT': output}
	processing.run('gdal:translate', translate_params)
	delete_aux([tmp_file])
	return output

def load_to_canvas(shaded_file,shaded_name):
	"""Add shaded bathymetry grids to map canvas"""
	shaded_layer = QgsRasterLayer(shaded_file, shaded_name, 'gdal')
	resampleFilter = shaded_layer.resampleFilter()
	resampleFilter.setZoomedInResampler(QgsBilinearRasterResampler())
	resampleFilter.setZoomedOutResampler(QgsBilinearRasterResampler())
	QgsProject.instance().addMapLayer(shaded_layer)

def delete_aux(list):
	"""Delete temporary files"""
	for file in list:
		if os.path.isfile(file):
			os.remove(file)

def create_combo_shaded(layer):
	"""Create slope and hillshade shaded RGB grid from layer input"""
	# get layer info
	base_path,base_name,ext = get_info_from_path(layer.source())
	
	# suffix for file name suggestion
	suffix = '_comboSHADED'
	
	# output path suggestion
	name = base_name + suffix
	path = os.path.join(base_path,name + extension)
	
	# finally, give user the choice for the output path
	title = 'Save Combo Shaded Bathymetry Grid'
	filter = 'GTiff (*.tif *.tiff)'
	output = select_ouput_file(title,path,filter)
	
	# get compression type from settings
	compress = get_compression_config()
	
	# get temporary folder
	temp_folder = QgsProcessingUtils.tempFolder()
	
	# render selected layer with defined symbology as rgb raster
	error, result = create_rgb(layer,temp_folder)
	if error:
		return error, result
	
	# get crs from layer
	crs = layer.crs()
	
	# get scale for vertical units
	scale = get_scale(crs)
	
	# create hillshade
	hs_file = get_out(temp_folder,'tmp_HS',extension)
	create_hs(layer,scale,hs_file,compress)
	
	# create slope
	slope_file = get_out(temp_folder,'tmp_SLOPE',extension)
	create_slope(layer,scale,slope_file,compress)
	
	# stretch slope to min max
	slope_stretch_file = get_out(temp_folder,'tmp_SLOPE_STRETCH',extension)
	stretch_min_max(slope_file,slope_stretch_file,compress)
	
	# invert slope (White to Black instead of Black to White)
	slope_inv_file = get_out(temp_folder,'tmp_SLOPE_INV',extension)
	create_inv(slope_stretch_file,slope_inv_file,compress)
	
	# shading computation
	syntax = 'uint8(((A/255.)*(((B*0.3)+(255.*0.7))/255.)*(((C*0.3)+(255.*0.7))/255.))*255)'
	shade(rgb_file,hs_file,slope_inv_file,syntax,temp_folder,output,compress)
	
	# load to QGIS canvas
	load_to_canvas(output,name)
	
	# delete auxillary files
	delete_aux([rgb_file, hs_file, slope_file, slope_stretch_file, slope_inv_file])
	
	return 0,shaded_file






































def create_combo_shaded2(layer):
	"""Create slope and hillshade shaded RGB grid from layer input"""
	suffix = '_comboSHADED'
	
	# get compression type from settings
	compress = get_compression_config()
	
	# get temporary folder
	temp_folder = QgsProcessingUtils.tempFolder()
	
	# render selected layer with defined symbology as rgb raster
	rgb_file = get_out(temp_folder,'tmp_RGB',extension)
	rgb_file = create_rgb(layer,temp_folder)
	if rgb_file == None:
		return 1, 'RGB file could not be rendered!'
	
	# get scale for vertical units
	scale = get_scale(crs)
	
	# create hillshade
	hs_file = get_out(temp_folder,'tmp_HS',extension)
	create_hs(layer,scale,hs_file,compress)
	
	# create slope
	slope_file = get_out(temp_folder,'tmp_SLOPE',extension)
	create_slope(layer,scale,slope_file,compress)
	
	# stretch slope to min max
	slope_stretch_file = get_out(temp_folder,'tmp_SLOPE_STRETCH',extension)
	stretch_min_max(slope_file,slope_stretch_file,compress)
	
	# invert slope (White to Black instead of Black to White)
	slope_inv_file = get_out(temp_folder,'tmp_SLOPE_INV',extension)
	create_inv(slope_stretch_file,slope_inv_file,compress)
	
	# output name and path for shaded grid
	shaded_name = base_name + suffix
	shaded_file = get_out(base_path,shaded_name,extension)
	
	# shading computation
	syntax = 'uint8(((A/255.)*(((B*0.3)+(255.*0.7))/255.)*(((C*0.3)+(255.*0.7))/255.))*255)'
	shade(rgb_file,hs_file,slope_inv_file,syntax,temp_folder,shaded_file,compress)
	
	# load to QGIS canvas
	load_to_canvas(shaded_file,shaded_name)
	
	# delete auxillary files
	delete_aux([rgb_file, hs_file, slope_file, slope_stretch_file, slope_inv_file])
	
	return 0,shaded_file

def create_hs_shaded(layer):
	"""Create hillshade shaded RGB grid from layer input"""
	suffix = '_hsSHADED'
	
	# get compression type from settings
	compress = get_compression_config()
	
	# get temporary folder
	temp_folder = QgsProcessingUtils.tempFolder()
	
	# render selected layer with defined symbology as rgb raster
	base_path,base_name,rgb_file,crs = create_rgb(layer,temp_folder)
	if rgb_file == None:
		return 1, 'RGB file could not be rendered!'
	
	# get scale for vertical units
	scale = get_scale(crs)
	
	# create hillshade
	hs_file = get_out(temp_folder,'tmp_HS',extension)
	create_hs(layer,scale,hs_file,compress)
	
	# output name and path for shaded grid
	shaded_name = base_name + suffix
	shaded_file = get_out(base_path,shaded_name,extension)
	
	# shading computation
	syntax = 'uint8(((A/255.)*(((B*0.5)+(255.*0.5))/255.))*255)'
	shade(rgb_file,hs_file,None,syntax,temp_folder,shaded_file,compress)
	
	# load to QGIS canvas
	load_to_canvas(shaded_file,shaded_name)
	
	# delete auxillary files
	delete_aux([rgb_file, hs_file])
	
	return 0,shaded_file

def create_slope_shaded(layer):
	"""Create slope shaded RGB grid from layer input"""
	suffix = '_slopeSHADED'
		
	# get compression type from settings
	compress = get_compression_config()
	
	# get temporary folder
	temp_folder = QgsProcessingUtils.tempFolder()
	
	# render selected layer with defined symbology as rgb raster
	base_path,base_name,rgb_file,crs = create_rgb(layer,temp_folder)
	if rgb_file == None:
		return 1, 'RGB file could not be rendered!'
	
	# get scale for vertical units
	scale = get_scale(crs)
	
	# create slope
	slope_file = get_out(temp_folder,'tmp_SLOPE',extension)
	create_slope(layer,scale,slope_file,compress)
	
	# stretch slope to min max
	slope_stretch_file = get_out(temp_folder,'tmp_SLOPE_STRETCH',extension)
	stretch_min_max(slope_file,slope_stretch_file,compress)
	
	# invert slope (White to Black instead of Black to White)
	slope_inv_file = get_out(temp_folder,'tmp_SLOPE_INV',extension)
	create_inv(slope_stretch_file,slope_inv_file,compress)
	
	# output name and path for shaded grid
	shaded_name = base_name + suffix
	shaded_file = get_out(base_path,shaded_name,extension)
	
	# shading computation
	syntax = 'uint8(((A/255.)*(((C*0.5)+(255.*0.5))/255.))*255)'
	shade(rgb_file,None,slope_inv_file,syntax,temp_folder,shaded_file,compress)
	
	# load to QGIS canvas
	load_to_canvas(shaded_file,shaded_name)
	
	# delete auxillary files
	delete_aux([rgb_file, slope_file, slope_stretch_file, slope_inv_file])
	
	return 0,shaded_file

def get_nodata_cell_count(raster, nodata, band_number):
	"""Get total cells, nodata cell count and percentage of nodata cells"""
	# get raster band as array
	band = raster.GetRasterBand(band_number).ReadAsArray()
	
	# count cells with individual values
	count = dict(zip(*np.unique(band, return_counts=True)))

	# get cell count with NoData values
	nodata_cells = count.get(nodata)
	# get overall cell count
	cells = band.size
	
	if nodata_cells != None:
		# compute percentage of cells with NoData values
		nodata_percentage = nodata_cells / cells
	else:
		nodata_cells = 0
		nodata_percentage = nodata_cells / cells
	
	return nodata_cells, cells, nodata_percentage

def get_area(layer,crs,extent,l):
	"""Calculate overall raster area based on ellipsoid"""
	# create CRS transformation
	trans = QgsCoordinateTransform(crs, QgsCoordinateReferenceSystem('EPSG:4326'), QgsProject.instance())
	
	# transform QgsRectangle to "EPSG:4236"
	geoRectangle = trans.transform(extent)
	
	# create geometry from QgsRectangle
	geometry = QgsGeometry().fromRect(geoRectangle)
	
	# calculate AREA
	area_m2 = l.measureArea(geometry)
	
	return area_m2

def calculate_raster_coverage(layer, band_number=1):
	"""Calculate data coverage of raster file"""
	provider = layer.dataProvider()
	
	# get CRS
	crs = layer.crs()
	
	# set project ellipsoid (for measurements) to CRS ellipsoid
	ellipsoid = QgsProject.instance().crs().ellipsoidAcronym()
	QgsProject.instance().setEllipsoid(ellipsoid)
	
	# calculate area of raster extent
	extent = layer.extent()
	
	# Initialize Distance calculator class
	l = QgsDistanceArea()
	l.setEllipsoid(ellipsoid)
	
	# get area
	area_m2 = get_area(layer,crs,extent,l)
	
	# check if NoData value is set
	if provider.sourceHasNoDataValue(band_number):
		# get NoData value for band
		nodata = provider.sourceNoDataValue(band_number)
		
		# get layer path
		path = layer.publicSource()
		# open raster file
		raster = gdal.Open(path, gdalconst.GA_ReadOnly)
		# get nodata cells, valid cells and nodata_percentage
		nodata_cells, cells, nodata_percentage = get_nodata_cell_count(raster, nodata, band_number=1)
		# close file
		raster = None
		
		# calclate DATA COVERAGE
		coverage = area_m2 * (1 - nodata_percentage)
		coverage_percentage = (1 - nodata_percentage)
		
		return area_m2, coverage, coverage_percentage
	else:
		iface.messageBar().pushMessage(u"Raster data coverage ", u"Missing NoData value(s) detected. Check settings of your raster layer!", level=Qgis.Info)
		return area_m2, area_m2, 1.0