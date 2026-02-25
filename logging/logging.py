import os

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
        # should be safe since button is disabled if PosiView is not enabled
        self.posiview = plugins['PosiView']

        # get PosiView Project
        self.posiview_project = self.posiview.project

    def get_devices(self):
        """Get PosiView devices (mobiles)."""
        # get PosiViewProject properties
        self.properties = self.posiview_project.properties()

        self.devices = self.properties['Mobiles']

        self.devices_names = list(self.devices.keys())

        self.device_properties = {d: self.devices[d].get('provider') for d in self.devices_names}
