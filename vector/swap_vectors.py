from pathlib import Path
import os

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsProcessingParameterVectorLayer

from qgis.PyQt.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon

from .vector import Vector
from .. import utils


class SwapVectors(QgsProcessingAlgorithm, Vector):
    """Swap Vectors."""

    # Processing parameters
    # inputs:
    INPUT = 'INPUT'
    SELECTED = 'SELECTED'
    # outputs:
    OUTPUT = 'OUTPUT'

    def __init__(self):
        """Initialize SwapVectors."""
        super(SwapVectors, self).__init__()

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                name=self.INPUT,
                description=self.tr('Input vector layer'),
                types=[QgsProcessing.SourceType.TypeVectorLine],
                defaultValue=None,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.SELECTED,
                description=self.tr('Swap only selected features'),
                optional=False,
                defaultValue=False)
        )

    def processAlgorithm(self, parameters, context, feedback):
        # get input variables as self.* for use in post-processing
        self.vector_layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        self.selected = self.parameterAsBoolean(parameters, self.SELECTED, context)

        feedback.pushConsoleInfo(self.tr('Swapping vectors...\n'))
        error, result = self.swap_vectors(self.vector_layer, selected=self.selected)
        if error:
            feedback.reportError(self.tr(result), fatalError=True)
            return {}

        self.vector_layer.triggerRepaint()

        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Swapped all those vectors!\n'))

        result = {self.OUTPUT: self.vector_layer}

        return result

    def name(self):
        return 'swapvectors'

    def icon(self):
        return QIcon(str(self.plugin_dir / 'icons' / 'swap_vectors.png'))

    def displayName(self):
        return self.tr('Swap Vectors')

    def group(self):
        return self.tr('Vector')

    def groupId(self):
        return 'vector'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        doc = Path(self.plugin_dir) / 'doc' / 'swap_vectors.help'
        if not doc.is_file():
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return SwapVectors()
