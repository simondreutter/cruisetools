import os

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterVectorLayer)

from qgis.PyQt.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon

from .vector import Vector
from .. import utils

class WriteLineLength(QgsProcessingAlgorithm, Vector):
    """Write Line Length."""

    # Processing parameters
    # inputs:
    INPUT = 'INPUT'
    M = 'M'
    KM = 'KM'
    NM = 'NM'
    # outputs:
    OUTPUT = 'OUTPUT'

    def __init__(self):
        """Initialize WriteLineLength."""
        super(WriteLineLength, self).__init__()
        
        # initialize default configuration
        self.initConfig()

    def initConfig(self):
        """Get default values from CruiseToolsConfig."""
        self.m = self.config.getboolean(self.module, 'm')
        self.km = self.config.getboolean(self.module, 'km')
        self.nm = self.config.getboolean(self.module, 'nm')

    def initAlgorithm(self, config=None):  # noqa
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                name=self.INPUT,
                description=self.tr('Input vector layer'),
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.M,
                description=self.tr('Meters'),
                optional=False,
                defaultValue=self.m)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.KM,
                description=self.tr('Kilometers'),
                optional=False,
                defaultValue=self.km)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.NM,
                description=self.tr('Nautical miles'),
                optional=False,
                defaultValue=self.nm)
        )

    def processAlgorithm(self, parameters, context, feedback):  # noqa
        # get input variables as self.* for use in post processing
        self.vector_layer = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        self.m = self.parameterAsBoolean(parameters, self.M, context)
        self.km = self.parameterAsBoolean(parameters, self.KM, context)
        self.nm = self.parameterAsBoolean(parameters, self.NM, context)
        
        # set new default values in config
        feedback.pushConsoleInfo(self.tr('Storing new default settings in config...'))
        self.config.set(self.module, 'm', self.m)
        self.config.set(self.module, 'km', self.km)
        self.config.set(self.module, 'nm', self.nm)
        
        result = {}
        
        return result

    def postProcessAlgorithm(self, context, feedback):  # noqa
        # layer in-place editing is not working very well in the processAlgortihm
        # therefore it was moved here to post processing
        
        # get project ellipsoid and transformContext for ellipsoidal measurements
        ellipsoid = context.project().crs().ellipsoidAcronym()
        transform_context = context.transformContext()
        
        # run the function from Vector base class
        feedback.pushConsoleInfo(self.tr('Adding length attributes...\n'))
        error, result = self.write_line_length(self.vector_layer, ellipsoid, transform_context, m=self.m, km=self.km, nm=self.nm)
        if error:
            feedback.reportError(self.tr(result), fatalError=True)
            return {}
        
        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Lengths are in!\n'))
        
        result = {self.OUTPUT : self.vector_layer}
        
        return result

    def name(self):  # noqa
        return 'writelinelength'

    def icon(self):  # noqa
        icon = QIcon(f'{self.plugin_dir}/icons/write_line_length.png')
        return icon

    def displayName(self):  # noqa
        return self.tr('Write Line Length')

    def group(self):  # noqa
        return self.tr('Vector')

    def groupId(self):  # noqa
        return 'vector'

    def tr(self, string):  # noqa
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):  # noqa
        doc = f'{self.plugin_dir}/doc/write_line_length.help'
        if not os.path.exists(doc):
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):  # noqa
        return WriteLineLength()
