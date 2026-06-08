from pathlib import Path

from .. import config


class Bathymetry(object):
    """Base class for bathymetry modules."""

    def __init__(self):
        """Initialize Bathymetry."""
        self.module = 'BATHYMETRY'
        self.config = config.CruiseToolsConfig()
        self.plugin_dir = Path(__file__).resolve().parent.parent
