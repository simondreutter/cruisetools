import os

from .. import config

class Contour(object):
    """Base class for contour modules."""

    def __init__(self):
        """Initialize Contour."""
        self.module = 'CONTOUR'
        self.config = config.CruiseToolsConfig()
        self.plugin_dir = f'{os.path.dirname(__file__)}/..'
