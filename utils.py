import datetime as dt
import math
from pathlib import Path
import random
import re

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

# import some tools
from qgis.core import *


def backup_file(file):
    """Backup existing file with timestamp.

    Parameters
    ----------
    file : pathlib.Path or str
        file to back up

    """
    file = Path(file)
    timestamp = dt.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = file.with_name(f'{file.name}.backup_{timestamp}')
    file.rename(backup)


def dd2ddm(latitude, longitude):
    """Convert decimal degree (DD) in degree and decimal minutes (DDM)

    Parameters
    ----------
    latitude : float
        latitude
    longitude : float
        longitude

    Returns
    -------
    lat_ddm, lon_ddm : (str, str)
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
    lat_ddm = f'{int(lat_degree):02d}°{round(lat_dminute, 3):06.3f}\'{hemisphere}'

    # longitude
    if longitude > 0.:
        hemisphere = 'E'
    elif longitude == 0.:
        hemisphere = ''
    else:
        hemisphere = 'W'
    lon_d_, lon_degree = math.modf(abs(longitude))
    lon_dminute = lon_d_ * 60
    lon_ddm = f'{int(lon_degree):03d}°{round(lon_dminute, 3):06.3f}\'{hemisphere}'

    return lat_ddm, lon_ddm


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
    file_path = Path(file_path)
    driver = None
    ext = file_path.suffix.upper()
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
    file_path = Path(file_path)
    base_path = str(file_path.parent.resolve())
    base_name = file_path.name
    ext = file_path.suffix

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
    path = Path(path)
    link = f'<a href="{path.parent}">{path}</a>'

    return link


def sanitize_filename(filename):
    """Sanitize filename.

    Parameters
    ----------
    filename : str
        input filename

    Returns
    -------
    filename : str
        sanitized filename

    """
    filename = str(filename).strip()
    filename = re.sub(r'[^\w\s-]', '', filename.lower())
    filename = re.sub(r'[-\s]+', '-', filename).strip('-_')
    return filename


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
