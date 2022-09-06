# -*- coding: utf-8 -*-
import os
import configparser

class CruiseToolsConfig:
    def __init__(self):
        """Initialize CruiseToolsConfig"""
        self.config_file = os.path.join(os.path.dirname(__file__), 'cruise_tools_config.ini')
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.initConfigFile()

    def initConfigFile(self):
        """Initialize configuration file

        Settings are grouped by Cruise Tools modules.
        Module / section name is upper(), option name is lower().
        
        [BATHYMETRY]
          colorramp     : default shading type (0: haxby, 1: blues, 2: rainbow)
          max           : depth range maximum (positive up)
          min           : depth range minimum (positive up)
          shader        : default shading type (0: hillshade, 1: slope, 2: combo)
        
        [CONTOUR]
          interval      : default interval for contours
        
        [VECTOR]
          latlon_dd     : default setting for writing Lat Lon DD coordinates
          latlon_ddm    : default setting for writing Lat Lon DDM coordinates
          xy            : default setting for writing projection XY coordinates
          m             : default setting for writing length in meters
          nm            : default setting for writing length in nautical miles
          km            : default setting for writing length in kilometers
          m2            : default setting for writing area in square meters
          km2           : default setting for writing area in square kilometers
        
        [PLANNING]
          file_type     : id of file type (0: point planning, 1: line planning)
          default_crs   : default CRS for XY coordinates
          mbes          : default setting to create MBES swath angle field or not
          export_format : default bridge export format (0: default csv, 1: SAM Route Exchange style CSV)
          swath_angle   : default swath angle for MBES coverage calculation

        """
        # if config file exists, read it
        if os.path.isfile(self.config_file):
            self.read()
        # if not, create a default one
        else:
            self.config['BATHYMETRY'] = {'color_ramp'    : 0,
                                         'max'           : 0,
                                         'min'           : -5000,
                                         'shader'        : 2}
            self.config['CONTOUR'] =    {'interval'      : 100}
            self.config['VECTOR'] =     {'latlon_dd'     : True,
                                         'latlon_ddm'    : True,
                                         'xy'            : False,
                                         'm'             : True,
                                         'nm'            : True,
                                         'km'            : True,
                                         'm2'            : False,
                                         'km2'           : True}
            self.config['PLANNING'] =   {'file_type'     : 0,
                                         'default_crs'   : 'EPSG:4326',
                                         'mbes'          : False,
                                         'vessel'        : 'DEFAULT',
                                         'export_format' : 0,
                                         'swath_angle'   : 120}
            self.write()
        
        return

    def get(self, section, option, fallback=None):
        """Get single option

        Parameters
        ----------
        section : str
            section name
        option : str
            option name
        fallback : str or float or int or boolean or None
            fallback value (Default value = None)

        Returns
        -------
        value : str
            value from configuration

        """
        section = section.upper()
        option = option.lower()
        value = self.config.get(section, option, fallback=fallback)
        return value

    def getint(self, section, option, fallback=None):
        """Return config value as integer if possible

        Parameters
        ----------
        section : str
            section name
        option : str
            option name
        fallback : str or float or int or boolean or None
            fallback value (Default value = None)

        Returns
        -------
        value : int or str
            value from configuration as int if possible

        """
        section = section.upper()
        option = option.lower()
        value = self.get(section, option, fallback=fallback)
        try:
            value = int(value)
        except ValueError:
            pass
        return value

    def getfloat(self, section, option, fallback=None):
        """Return config value as float if possible

        Parameters
        ----------
        section : str
            section name
        option : str
            option name
        fallback : str or float or int or boolean or None
            fallback value (Default value = None)

        Returns
        -------
        value : float or str
            value from configuration as float if possible

        """
        section = section.upper()
        option = option.lower()
        value = self.get(section, option, fallback=fallback)
        try:
            value = float(value)
        except ValueError:
            pass
        return value

    def getboolean(self, section, option, fallback=None):
        """Return config value as boolean if possible

        Parameters
        ----------
        section : str
            section name
        option : str
            option name
        fallback : str or float or int or boolean or None
            fallback value (Default value = None)

        Returns
        -------
        value : boolean or str
            value from configuration as boolean if possible

        """
        section = section.upper()
        option = option.lower()
        value = self.get(section, option, fallback=fallback)
        if value.lower() in ['1', 'true', 't', 'yes', 'y', 'yeah', 'on']:
            return True
        elif value.lower() in ['0', 'false', 'f', 'no', 'n', 'nope', 'off']:
            return False
        else:
            return value

    def set(self, section, option, value):
        """Set value for section/option

        Parameters
        ----------
        section : str
            section name
        option : str
            option name
        value : str or float or int or boolean or None
            value to set

        """
        section = section.upper()
        option = option.lower()
        if not isinstance(value, str):
            value = str(value)
        if self.config.has_option(section, option):
            self.config.set(section, option, value)
            self.write()
        else:
            print(f'"[{section}]/{option}" is no valid option in the configuration.')
        
        return

    def get_minmax(self):
        """Convenience function to return bathymetry min max values"""
        min = self.getint('BATHYMETRY', 'MIN')
        max = self.getint('BATHYMETRY', 'MAX')
        return min, max

    def read(self):
        """Read configuration file"""
        self.config.read(self.config_file)
        return

    def write(self):
        """Write configuration file"""
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)
        return
