# -*- coding: utf-8 -*-
import os

from qgis.core import (
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingUtils,
    QgsWkbTypes)

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from PyQt5.QtGui import QIcon

from .planning import Planning
from .. import utils

class PlanningLinesToVertices(QgsProcessingAlgorithm,Planning):
    '''Planning Lines To Vertices'''
    #processing parameters
    # inputs:
    INPUT = 'INPUT'
    # outputs:
    OUTPUT = 'OUTPUT'

    def __init__(self):
        '''Initialize PlanningLinesToVertices'''
        super(PlanningLinesToVertices, self).__init__()
        
        # style files for planning layer
        self.style_planning_lines_vertices = ':/plugins/cruisetools/styles/style_planning_lines_to_vertices.qml'

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.INPUT,
                description=self.tr('Input Line Planning Layer'),
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.OUTPUT,
                description=self.tr('Planning Line Vertices'),
                type=QgsProcessing.TypeVectorLine,
                defaultValue=None,
                optional=False,
                createByDefault=True)
        )

    def processAlgorithm(self, parameters, context, feedback):
        # get input variables
        source = self.parameterAsSource(parameters,self.INPUT,context)
        
        # fields to be created (empty)
        feedback.pushConsoleInfo(self.tr(f'Creating attribute fields...'))
        fields = QgsFields()
        
        # fields from feature source
        source_fields = source.fields()
        
        # if source does not have fid field, create it in fields
        if 'fid' not in source_fields.names():
            fields.append(QgsField('fid',QVariant.Int,'',4,0))
        
        # add all fields from source to fields variable
        for field in source_fields:
            fields.append(field)
        
        # creating feature sink for vertices
        feedback.pushConsoleInfo(self.tr(f'Creating feature sink...'))
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               fields, QgsWkbTypes.Point, source.sourceCrs())
        
        # get features from source
        features = source.getFeatures()
        
        # get vertices from features
        vertices = self.lines_to_vertices(features,fields)
        
        # write vertex features to sink
        sink.addFeatures(vertices, QgsFeatureSink.FastInsert)
        
        # make variables accessible for post processing
        self.output = dest_id
        
        result = {self.OUTPUT : self.output}
        
        return result

    def postProcessAlgorithm(self, context, feedback):
        # get layer from source and context
        planning_layer = QgsProcessingUtils.mapLayerFromString(self.output, context)
        
        # loading Cruise Tools Planning style from QML style file
        feedback.pushConsoleInfo(self.tr(f'Loading style...'))
        planning_layer.loadNamedStyle(self.style_planning_lines_vertices)
        
        # writing style to GPKG (or else)
        style_name = 'Cruise Tools Planning Vertices'
        style_desc = 'Planning Vertices style for QGIS Symbology from Cruise Tools plugin'
        
        feedback.pushConsoleInfo(self.tr(f'Writing style to output...\n'))
        planning_layer.saveStyleToDatabase(name=style_name, description=style_desc, useAsDefault=True, uiFileContent=None)
        
        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Vertices file created!\n'))
        
        result = {self.OUTPUT : self.output}
        
        return result

    def name(self):
        return 'planninglinestovertices'

    def icon(self):
        icon = QIcon(f'{self.plugin_dir}/icons/planning_lines_to_vertices.png')
        return icon

    def displayName(self):
        return self.tr('Planning Lines To Vertices')

    def group(self):
        return self.tr('Planning')

    def groupId(self):
        return 'planning'

    def tr(self, string):
        return QCoreApplication.translate('Processing',string)

    def shortHelpString(self):
        doc = f'{self.plugin_dir}/doc/planning_lines_to_vertices.help'
        if not os.path.exists(doc):
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return PlanningLinesToVertices()
