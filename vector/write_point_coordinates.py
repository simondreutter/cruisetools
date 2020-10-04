# -*- coding: utf-8 -*-
import os
import processing

from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterCrs,
    QgsProcessingParameterVectorLayer)

from qgis.PyQt.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon

from .vector import Vector
from .. import config
from .. import utils

class WritePointCoordinates(QgsProcessingAlgorithm,Vector):
    '''Write Point Coordinates'''
    #processing parameters
    # inputs:
    INPUT = 'INPUT'
    LATLON_DD = 'LATLON_DD'
    LATLON_DDM = 'LATLON_DDM'
    XY = 'XY'
    CRS_XY = 'CRS_XY'
    # outputs:
    OUTPUT = 'OUTPUT'

    def __init__(self):
        '''Initialize WritePointCoordinates'''
        super(WritePointCoordinates, self).__init__()
        
        # initialize default configuration
        self.initConfig()

    def initConfig(self):
        '''Get default values from CruiseToolsConfig'''
        self.latlon_dd = self.config.getboolean(self.module,'latlon_dd')
        self.latlon_ddm = self.config.getboolean(self.module,'latlon_ddm')
        self.xy = self.config.getboolean(self.module,'xy')

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                name=self.INPUT,
                description=self.tr('Input Vector Layer'),
                types=[QgsProcessing.TypeVectorPoint],
                defaultValue=None,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.LATLON_DD,
                description=self.tr('Lat Lon / Decimal Degrees [ EPSG:4326 ]'),
                optional=False,
                defaultValue=self.latlon_dd)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.LATLON_DDM,
                description=self.tr('Lat Lon / Degrees Decimal Minutes [ EPSG:4326 ]'),
                optional=False,
                defaultValue=self.latlon_ddm)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.XY,
                description=self.tr('XY Coordinates'),
                optional=False,
                defaultValue=self.xy)
        )
        self.addParameter(
            QgsProcessingParameterCrs(
                name=self.CRS_XY,
                description=self.tr('XY in CRS (Default: Layer CRS)'),
                optional=True,
                defaultValue=None)
        )

    def processAlgorithm(self, parameters, context, feedback):
        # get input variables as self.* for use in post processing
        self.vector_layer = self.parameterAsVectorLayer(parameters,self.INPUT,context)
        self.latlon_dd = self.parameterAsBoolean(parameters,self.LATLON_DD,context)
        self.latlon_ddm = self.parameterAsBoolean(parameters,self.LATLON_DDM,context)
        self.xy = self.parameterAsBoolean(parameters,self.XY,context)
        self.crs_xy = self.parameterAsCrs(parameters,self.CRS_XY,context)
        
        # set new default values in config
        feedback.pushConsoleInfo(self.tr(f'Storing new default settings in config...'))
        self.config.set(self.module,'latlon_dd',self.latlon_dd)
        self.config.set(self.module,'latlon_ddm',self.latlon_ddm)
        self.config.set(self.module,'xy',self.xy)
        
        result = {}
        
        return result

    def postProcessAlgorithm(self, context, feedback):
        # layer in-place editing is not working very well in the processAlgortihm
        # therefor it was moved here to post processing
        
        # get project transformContext for ellipsoidal measurements
        transform_context = context.transformContext()
        
        # run the function from Vector base class
        feedback.pushConsoleInfo(self.tr(f'Adding coordinate attributes...\n'))
        error, result = self.write_point_coordinates(self.vector_layer,transform_context,self.latlon_dd,self.latlon_ddm,self.xy,self.crs_xy)
        if error:
            feedback.reportError(self.tr(result),fatalError=True)
            return {}
        
        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Coordinates are in!\n'))
        
        result = {self.OUTPUT : self.vector_layer}
        
        return result

    def name(self):
        return 'writepointcoordinates'

    def icon(self):
        icon = QIcon(f'{self.plugin_dir}/icons/write_point_coordinates.png')
        return icon

    def displayName(self):
        return self.tr('Write Point Coordinates')

    def group(self):
        return self.tr('Vector')

    def groupId(self):
        return 'vector'

    def tr(self, string):
        return QCoreApplication.translate('Processing',string)

    def shortHelpString(self):
        doc = f'{self.plugin_dir}/doc/write_point_coordinates.help'
        if not os.path.exists(doc):
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return WritePointCoordinates()
