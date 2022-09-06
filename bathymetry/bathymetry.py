# -*- coding: utf-8 -*-
import os

from .. import config

class Bathymetry(object):
    """Base class for bathymetry modules"""

    def __init__(self):
        """Initialize Bathymetry"""
        self.module = 'BATHYMETRY'
        self.config = config.CruiseToolsConfig()
        self.plugin_dir = f'{os.path.dirname(__file__)}/..'
