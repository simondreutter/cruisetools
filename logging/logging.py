import os
from pprint import pprint

from qgis.core import QgsProject
from qgis.utils import iface, plugins

from ..config import CruiseToolsConfig

class Logging(object):
    """Base class for Logging."""

    def __init__(self):
        """Initialize Capture Position."""
        self.iface = iface
        
        self.project = QgsProject.instance()
        
        self.module = 'LOGGING'
        
        self.plugin_dir = f'{os.path.dirname(__file__)}/..'
        
        self.config = CruiseToolsConfig()
        
        # init PosiView
        self.access_posiview()
        
        # get devices
        self.get_devices()
        
    def access_posiview(self, reload_settings: bool = False):
        """Access PosiView plugin instance."""
        # should be save since button is disabled if PosiView is not enabled
        self.posiview = plugins['PosiView']
        
        # get PosiView Project
        self.posiview_project = self.posiview.project
        
    def get_devices(self):
        """Get PosiView devices (mobiles)."""
        # get PosiViewProject properties
        self.properties = self.posiview_project.properties()
        
        self.devices = self.properties['Mobiles']
        # for d, v in self.devices.items():
        #     print(d, v)
        
        self.devices_names = list(self.devices.keys())
        # print(self.devices_names)
        
        self.device_properties = {d: self.devices[d].get('provider') for d in self.devices_names}
        # pprint(self.device_properties)
