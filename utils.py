# -*- coding: utf-8 -*-
'''
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
'''
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# import some tools
from qgis.core import *
import math
import os
import random

def dd2ddm(latitude, longitude):
    '''Convert decimal degree (DD) in degree and decimal minutes (DDM)'''
    # latitude
    if latitude > 0.:
        hemisphere = 'N'
    elif latitude == 0.:
        hemisphere = ''
    else:
        hemisphere = 'S'
    lat_d_, lat_degree = math.modf(abs(latitude))
    lat_dminute = lat_d_ * 60
    lat_DDM = f'{int(lat_degree):02d}°{round(lat_dminute,3):06.3f}\'{hemisphere}'
    
    # longitude
    if longitude > 0.:
        hemisphere = 'E'
    elif longitude == 0.:
        hemisphere = ''
    else:
        hemisphere = 'W'
    lon_d_, lon_degree = math.modf(abs(longitude))
    lon_dminute = lon_d_ * 60
    lon_DDM = f'{int(lon_degree):03d}°{round(lon_dminute,3):06.3f}\'{hemisphere}'
    
    return lat_DDM, lon_DDM

def get_features(layer,selected=True):
    '''Get features from vector layer.'''
    # check if any features are selected and only use those in that case
    if (layer.selectedFeatureCount() == 0) or (selected == False):
        features = layer.getFeatures()
    elif layer.selectedFeatureCount() > 0:
        features = layer.getSelectedFeatures()
    
    return features

def mkdir(directory):
    '''Create a new folder if it doesn't exist already'''
    if not os.path.isdir(directory):
        os.makedirs(directory)
    
    return directory

def select_output_file(title,path,filter):
    '''Select output file'''
    if title == None:
        title = 'Export'
    if path == None:
        path = QgsProject.instance().homePath()
    dialog = QFileDialog()
    f, _filter = QFileDialog.getSaveFileName(dialog, title, path, filter)
    if f == '':
        return 1, None
    
    return 0, f

def select_input_file(title,path,filter):
    '''Select input file'''
    if title == None:
        title = 'Import'
    if path == None:
        path = QgsProject.instance().homePath()
    dialog = QFileDialog()
    f, _filter = QFileDialog.getOpenFileName(dialog, title, path, filter)
    if f == '':
        return 1, None
    
    return 0, f

def get_driver_from_path(file_path):
    '''Get GDAL driver from file path'''
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
    '''Get file info from file path'''
    file_info = QFileInfo(file_path)
    # base path to create contours directory
    base_path = file_info.absolutePath()
    # base name for output
    base_name = file_info.baseName()
    # extension
    ext = os.path.splitext(file_path)[1]
    
    return base_path,base_name,ext

def return_file_link(path):
    '''Return link to file base directory for messageBar'''
    return f'<a href="{os.path.dirname(path)}">{path}</a>'

def return_success():
    '''Return success message'''
    success_messages = ['Aye',
                        'BOING',
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
                        'Noice',
                        'Rasiert',
                        'Score',
                        'Sweet',
                        'Turbo',
                        'Turbo Nice',
                        'Ultron'
                        'Whoop',
                        'Yeah',
                        'Yiihaa']
    success_message = random.choice(success_messages)
    
    return success_message
