# -*- coding: utf-8 -*-
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# import some tools
from qgis.core import *
import os
import processing

# import Cruise Tools modules
from .utils import *
from .vector import *

style_contours = ':/plugins/cruisetools/styles/style_contours.qml'

def create_contours(layer,interval):
    '''Create contour lines from input raster layer'''
    # get layer info
    base_path,base_name,ext = get_info_from_path(layer.source())
    
    # compile contour name from original filename plus suffix containing contour interval
    contour_name = base_name + '_contour_' + str(interval) + 'm'
    
    # contour_file (with extension)
    contour_file = contour_name + '.gpkg'
    
    # output path suggestion
    path = os.path.join(base_path,contour_file)
    
    # finally, give user the choice for the output path
    title = 'Save Contour File'
    filter = 'GeoPackage (*.gpkg);;ESRI Shapefile (*.shp)'
    error, output = select_output_file(title,path,filter)
    if error:
        return error, 'No output file selected!'
    
    # get output file extension (.gpkg or .shp)
    contours_extension = get_info_from_path(output)[2]
    
    # get temporary folder
    temp_folder = QgsProcessingUtils.tempFolder()
    contours_tmp = os.path.join(temp_folder,'tmp_contours' + contours_extension)
    
    # get CRS from raster file (for some reasons gdal:contour is assigning a false CRS otherwise...)
    crs = layer.crs()
    
    # parameters for contour algortihm
    params_contour = {'INPUT': layer,
                        'BAND': 1,
                        'INTERVAL': interval,
                        'FIELD_NAME': 'ELEV',
                        'CREATE_3D': False,
                        'IGNORE_NODATA': False,
                        'NODATA': layer.dataProvider().sourceNoDataValue(1), # 1 -> band number
                        'OFFSET': 0,
                        'OUTPUT':contours_tmp}
    processing.run('gdal:contour', params_contour)
    
    # parameters for smoothing
    params_smooth = {'INPUT': contours_tmp,
                        'ITERATIONS' : 3,
                        'MAX_ANGLE' : 180,
                        'OFFSET' : 0.25,
                        'OUTPUT': output}
    processing.run('native:smoothgeometry', params_smooth)
    
    # load contours from file
    contours_layer = QgsVectorLayer(output, contour_name, 'ogr')
    
    # set original CRS
    contours_layer.setCrs(crs)
    
    # add to canvas
    QgsProject.instance().addMapLayer(contours_layer)
    
    # write line lengths to table in order to filter short lines
    error, result = write_line_length(contours_layer,True,False)
    
    # bathy grids are often Z +down so the vectors need to be swapped
    error, result = swap_vectors(contours_layer, selected=False)
    
    # load contour style from style file
    contours_layer.loadNamedStyle(style_contours)
    
    # filter contours by lengths
    length_filter = f'length_m > {interval * 5}'
    contours_layer.setSubsetString(length_filter)
    
    return 0, output
