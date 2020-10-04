# -*- coding: utf-8 -*-
import os
import processing

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterVectorLayer)

from qgis.PyQt.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon

from .vector import Vector
from .. import config
from .. import utils

class WritePolygonArea(QgsProcessingAlgorithm,Vector):
    '''Write Polygon Area'''
    #processing parameters
    # inputs:
    INPUT = 'INPUT'
    M2 = 'M2'
    KM2 = 'KM2'
    # outputs:
    OUTPUT = 'OUTPUT'

    def __init__(self):
        '''Initialize WritePolygonArea'''
        super(WritePolygonArea, self).__init__()
        
        # initialize default configuration
        self.initConfig()

    def initConfig(self):
        '''Get default values from CruiseToolsConfig'''
        self.m2 = self.config.getboolean(self.module,'m2')
        self.km2 = self.config.getboolean(self.module,'km2')

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                name=self.INPUT,
                description=self.tr('Input Vector Layer'),
                types=[QgsProcessing.TypeVectorPolygon],
                defaultValue=None,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.M2,
                description=self.tr('Square Meters'),
                optional=False,
                defaultValue=self.m2)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.KM2,
                description=self.tr('Square Kilometers'),
                optional=False,
                defaultValue=self.km2)
        )

    def processAlgorithm(self, parameters, context, feedback):
        # get input variables as self.* for use in post processing
        self.vector_layer = self.parameterAsVectorLayer(parameters,self.INPUT,context)
        self.m2 = self.parameterAsBoolean(parameters,self.M2,context)
        self.km2 = self.parameterAsBoolean(parameters,self.KM2,context)
        
        # set new default values in config
        feedback.pushConsoleInfo(self.tr(f'Storing new default settings in config...'))
        self.config.set(self.module,'m2',self.m2)
        self.config.set(self.module,'km2',self.km2)
        
        result = {}
        
        return result

    def postProcessAlgorithm(self, context, feedback):
        # layer in-place editing is not working very well in the processAlgortihm
        # therefor it was moved here to post processing
        
        # get project ellipsoid and transformContext for ellipsoidal measurements
        ellipsoid = context.project().crs().ellipsoidAcronym()
        transform_context = context.transformContext()
        
        # run the function from Vector base class
        feedback.pushConsoleInfo(self.tr(f'Adding area attributes...\n'))
        error, result = self.write_polygon_area(self.vector_layer,ellipsoid,transform_context,m2=self.m2,km2=self.km2)
        if error:
            feedback.reportError(self.tr(result),fatalError=True)
            return {}
        
        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Areas are in!\n'))
        
        result = {self.OUTPUT : self.vector_layer}
        
        return result
    
    def name(self):
        return 'writepolygonarea'

    def icon(self):
        icon = QIcon(f'{self.plugin_dir}/icons/write_polygon_area.png')
        return icon

    def displayName(self):
        return self.tr('Write Polygon Area')

    def group(self):
        return self.tr('Vector')

    def groupId(self):
        return 'vector'

    def tr(self, string):
        return QCoreApplication.translate('Processing',string)

    def shortHelpString(self):
        doc = f'{self.plugin_dir}/doc/write_polygon_area.help'
        if not os.path.exists(doc):
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return WritePolygonArea()
