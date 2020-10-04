# -*- coding: utf-8 -*-
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# import some tools
import os
import configparser

settings_file = os.path.join(os.path.dirname(__file__), 'config', 'settings.ini')

def init_settings():
    '''Initialize configuration file'''
    if os.path.isfile(settings_file):
        return True
    else:
        config = configparser.ConfigParser()
        config['VESSEL'] = {'vessel' : 'default'}
        config['COMPRESSION'] = {'type' : 'DEFLATE'}
        config['BATHYMETRY'] = {'colors' : 'Haxby',
                                'max' : '-5000',
                                'min' : '0'}
        write_settings(config)
        return False

def get_vessel_config():
    '''Return vessel configuration'''
    config = configparser.ConfigParser()
    config.read(settings_file)
    return config['VESSEL']['vessel']

def get_compression_config():
    '''Return compression configuration'''
    config = configparser.ConfigParser()
    config.read(settings_file)
    return config['COMPRESSION']['type']

def get_colors_config():
    '''Return colors configuration'''
    config = configparser.ConfigParser()
    config.read(settings_file)
    colors_key = config['BATHYMETRY']['colors']
    colors_dict = {
                'Haxby':['#2539af','#287ffb','#32beff','#6aebff','#8aecae','#cdffa2','#f0ec79','#ffbd57','#ffa144','#ffba85','#ffffff'],
                'Blues':['#08306b','#08519c','#1c6cb1','#3585c0','#529dcc','#73b3d8','#9ac8e1','#bad6eb','#d1e3f3','#e4eff9','#f7fbff'],
                'Rainbow':['#640065','#7b0090','#8200b8','#7c00de','#6500ff','#3700ff','#0009ff','#004aff','#007eff','#00acff','#00d8ff','#00fff8','#00ff8a','#05ff00','#38ff00','#5fff00','#83ff00','#a4ff00','#c4ff00','#e3ff00','#fffd00','#ffdd00','#ffbc00','#ff9900','#ff7400','#ff4c00','#ff1e00','#ff0000','#ff0000','#ff0000','#ff0000','#ff0000','#ff0000','#ec0000','#da0000','#c70000','#b40000','#a00000','#8c0000','#770000','#610000']
                }
    return colors_dict[colors_key]

def get_minmax_config():
    '''Return compression configuration'''
    config = configparser.ConfigParser()
    config.read(settings_file)
    return config['BATHYMETRY']['min'],config['BATHYMETRY']['max']

def read_settings():
    '''Return configuration values'''
    config = configparser.ConfigParser()
    config.read(settings_file)
    return config

def write_settings(config):
    '''Write configuration file'''
    with open(settings_file,'w') as configfile:
        config.write(configfile)
    return
