from pathlib import Path

from .. import config


class Contour(object):
    """Base class for contour modules."""

    def __init__(self):
        """Initialize Contour."""
        self.module = 'CONTOUR'
        self.config = config.CruiseToolsConfig()
        self.plugin_dir = Path(__file__).resolve().parent.parent
