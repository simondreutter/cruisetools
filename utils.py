from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# import some tools
from qgis.core import *
import os
import random
import math

def dd2ddm(latitude,longitude):
    """Convert decimal degree (DD) in degree and decimal minutes (DDM)

    Parameters
    ----------
    latitude : float
        latitude
    longitude : float
        longitude

    Returns
    -------
    lat_DDM, lon_DDM : (str, str)
        latitude, longitude as DDM strings

    """
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

def get_driver_from_path(file_path):
    """Get GDAL driver from file path

    Parameters
    ----------
    file_path : str
        input file path

    Returns
    -------
    driver : str
        GDAL driver name

    """
    driver = None
    ext = os.path.splitext(file_path)[1].upper()
    if '.TIF' in ext:
        driver = 'GTiff'
    elif ext == '.GPKG':
        driver = 'GPKG'
    elif ext == '.SHP':
        driver = 'ESRI Shapefile'
    elif ext == '.XLSX':
        driver = 'xlsx'
    
    return driver

def get_info_from_path(file_path):
    """Get file info from file path

    Parameters
    ----------
    file_path : str
        input file path

    Returns
    -------
    base_path,base_name,ext : (str,str,str)
        base path, base name, and extension

    """
    file_info = QFileInfo(file_path)
    base_path = file_info.absolutePath()
    base_name = file_info.baseName()
    ext = os.path.splitext(file_path)[1]
    
    return base_path, base_name, ext

def return_file_link(path):
    """Return HTML link to file from file path

    Parameters
    ----------
    path : str
        path to file

    Returns
    -------
    link: str
        HTML link to base path

    """
    link = f'<a href="{os.path.dirname(path)}">{path}</a>'
    
    return link

def return_success():
    """Return an awesome success message for Cruise Tools"""
    success_messages = ['Aye',
                        'BOING',
                        'Boom',
                        'Cool',
                        'Çüş',
                        'Cute',
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
                        'Ultron',
                        'Whoop',
                        'Yeah',
                        'Yiihaa',
                        'Zweet']
    success_message = random.choice(success_messages)
    
    return success_message
