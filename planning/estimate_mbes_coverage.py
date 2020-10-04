# -*- coding: utf-8 -*-
import os
from math import tan, radians

from qgis.core import (
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsDistanceArea,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsGeometry,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterBand,
    QgsProcessingUtils,
    QgsWkbTypes)

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from PyQt5.QtGui import QIcon

from .planning import Planning
from .. import config
from .. import utils

class EstimateMBESCoverage(QgsProcessingAlgorithm,Planning):
    '''Estimate MBES Coverage'''
    #processing parameters
    # inputs:
    INPUT_LINE = 'INPUT_LINE'
    INPUT_RASTER = 'INPUT_RASTER'
    BAND = 'BAND'
    SWATH_ANGLE_FIELD = 'SWATH_ANGLE_FIELD'
    SWATH_ANGLE = 'SWATH_ANGLE'
    # outputs:
    OUTPUT = 'OUTPUT'

    def __init__(self):
        '''Initialize CreatePlanningFile'''
        super(EstimateMBESCoverage, self).__init__()
        
        # style files for mbes coverage layers
        self.style_mbes_coverage = ':/plugins/cruisetools/styles/style_mbes_coverage.qml'
        self.style_mbes_coverage_vertices = ':/plugins/cruisetools/styles/style_mbes_coverage_vertices.qml'
        
        # distance for line densifier
        self.vertex_distance = 50 # m
        
        # initialize default configuration
        self.initConfig()

    def initConfig(self):
        '''Get default values from CruiseToolsConfig'''
        self.swath_angle = self.config.getint(self.module,'swath_angle')

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.INPUT_LINE,
                description=self.tr('Input MBES Line Planning Layer'),
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterField(
                name=self.SWATH_ANGLE_FIELD,
                description=self.tr('Swath Angle Field'),
                defaultValue='mbes_swath_angle',
                parentLayerParameterName=self.INPUT_LINE,
                type=QgsProcessingParameterField.Numeric,
                allowMultiple=False,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.SWATH_ANGLE,
                description=self.tr('Swath Angle (fallback)'),
                type=QgsProcessingParameterNumber.Integer,
                optional=True,
                defaultValue=self.swath_angle,
                minValue=10,
                maxValue=160)
        )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                name=self.INPUT_RASTER,
                description=self.tr('Input Bathymetry Raster Layer'),
                defaultValue=None,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBand(
                name=self.BAND,
                description=self.tr('Band Number'),
                defaultValue=1,
                parentLayerParameterName=self.INPUT_RASTER,
                optional=False,
                allowMultiple=False)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.OUTPUT,
                description=self.tr('MBES Coverage'),
                type=QgsProcessing.TypeVectorPolygon,
                defaultValue=None,
                optional=False,
                createByDefault=True)
        )

    def processAlgorithm(self, parameters, context, feedback):
        # get input variables
        source = self.parameterAsSource(parameters,self.INPUT_LINE,context)
        swath_angle_field = self.parameterAsString(parameters,self.SWATH_ANGLE_FIELD,context)
        swath_angle_fallback = self.parameterAsInt(parameters,self.SWATH_ANGLE,context)
        raster_layer = self.parameterAsRasterLayer(parameters,self.INPUT_RASTER,context)
        band_number = self.parameterAsInt(parameters,self.BAND,context)
        
        # copy of the field name for later
        swath_angle_field_name = swath_angle_field
        
        # set new default values in config
        feedback.pushConsoleInfo(self.tr(f'Storing new default settings in config...'))
        self.config.set(self.module,'swath_angle',swath_angle_fallback)
        
        # get crs's
        crs_line = source.sourceCrs()
        crs_raster = raster_layer.crs()
        
        # get project transform_context
        transform_context = context.transformContext()
        
        # CRS transformation to "WGS84/World Mercator" for MBES coverage operations
        crs_mercator = QgsCoordinateReferenceSystem('EPSG:3395')
        trans_line2merc = QgsCoordinateTransform(crs_line, crs_mercator, transform_context)
        
        # CRS transformation to raster layer CRS for depth sampling
        trans_merc2raster = QgsCoordinateTransform(crs_mercator, crs_raster, transform_context)
        trans_line2raster = QgsCoordinateTransform(crs_line, crs_raster, transform_context)
        crs_geo = QgsCoordinateReferenceSystem('EPSG:4326')
        trans_line2geo = QgsCoordinateTransform(crs_line, crs_geo, transform_context)
        
        # initialize distance tool
        da = QgsDistanceArea()
        da.setSourceCrs(crs_mercator, transform_context)
        da.setEllipsoid(crs_mercator.ellipsoidAcronym())
        
        # empty lists for unioned buffers
        buffer_union_list = []
        
        # get (selected) features
        features = source.getFeatures()
        
        # feedback
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        
        # loop through features
        feedback.pushConsoleInfo(self.tr(f'Densifying line features...'))
        feedback.pushConsoleInfo(self.tr(f'Extracting vertices...'))
        feedback.pushConsoleInfo(self.tr(f'Sampling values...'))
        feedback.pushConsoleInfo(self.tr(f'Computing depth dependent buffers...'))
        feedback.pushConsoleInfo(self.tr(f'Unionizing output features...'))
        for feature_id, feature in enumerate(features):
            # get feature geometry
            feature_geom = feature.geometry()
            
            # check for LineString geometry
            if QgsWkbTypes.isSingleType(feature_geom.wkbType()):
                # get list of vertices
                vertices_list = feature_geom.asPolyline()
                vertices_list = [vertices_list]
            
            # check for MultiLineString geometry
            elif QgsWkbTypes.isMultiType(feature_geom.wkbType()):
                # get list of list of vertices per multiline part
                vertices_list = feature_geom.asMultiPolyline()
            
            for part_id, vertices in enumerate(vertices_list): 
                # transform vertices CRS to "WGS 84 / World Mercator"
                vertices_t = []
                for vertex in vertices:
                    vertex_trans = trans_line2merc.transform(vertex)
                    vertices_t.append(vertex_trans)
                
                # get centroid as point for UTM zone selection
                centroid = feature_geom.centroid()
                centroid_point = centroid.asPoint()
                
                # check if centroid needs to be transformed to get x/y in lon/lat
                if not crs_line.isGeographic():
                    centroid_point = trans_line2geo.transform(centroid_point)
                
                # get UTM zone of feature for buffering
                lat, lon = centroid_point.y(), centroid_point.x()
                crs_utm = self.get_UTM_zone(lat, lon)
                
                # create back and forth transformations for later
                trans_merc2utm = QgsCoordinateTransform(crs_mercator, crs_utm, transform_context)
                trans_utm2line = QgsCoordinateTransform(crs_utm, crs_line, transform_context)
                
                # split line into segments
                for segment_id in range(len(vertices_t) - 1):
                    # ===== (1) DENSIFY LINE VERTICES =====
                    # create new Polyline geometry for line segment
                    segment_geom = QgsGeometry.fromPolylineXY([vertices_t[segment_id], vertices_t[segment_id+1]])
                    
                    # measure ellipsoidal distance between start and end vertex
                    segment_length = da.measureLength(segment_geom)
                    
                    # calculate number of extra vertices to insert
                    extra_vertices = int(segment_length // self.vertex_distance)
                    
                    # create additional vertices along line segment
                    segment_geom_dense = segment_geom.densifyByCount(extra_vertices - 1)
                    
                    # initialize additional fields
                    feature_id_field = QgsField('feature_id',QVariant.Int,'Integer',len=5,prec=0)
                    part_id_field = QgsField('part_id',QVariant.Int,'Integer',len=5,prec=0)
                    segment_id_field = QgsField('segment_id',QVariant.Int,'Integer',len=5,prec=0)
                    
                    # list for segment buffers
                    buffer_list = []
                    
                    # loop over all vertices of line segment
                    for i, vertex in enumerate(segment_geom_dense.vertices()):
                        # === CREATE POINT FEATURE ===
                        # initialize feature and set geometry
                        fpoint = QgsFeature()
                        fpoint.setGeometry(vertex)
                        
                        # sample bathymetry grid
                        # get point geometry (as QgsPointXY)
                        fpoint_geom = fpoint.geometry()
                        pointXY = fpoint_geom.asPoint()
                        
                        # transform point to raster CRS
                        pointXY_raster = trans_merc2raster.transform(pointXY) #trans_line2raster.transform(pointXY)
                        
                        # sample raster at point location
                        pointXY_depth, error_check = raster_layer.dataProvider().sample(pointXY_raster, 1)
                        
                        # check if valid depth was sampled, otherwise skip point
                        if error_check == False:
                            continue
                        
                        # create depth-dependant buffer:
                        # check if swath_angle field is selected
                        if swath_angle_field != '':
                            # get value from field
                            swath_angle_field_value = feature.attribute(swath_angle_field)
                            # check if value is set (not NOLL)
                            if swath_angle_field_value == None:
                                # if NULL, set fallback
                                swath_angle = swath_angle_fallback
                            else:
                                # othervise take value from field
                                swath_angle = swath_angle_field_value
                        # or if no field was selected use fallback value right away
                        else:
                            swath_angle = swath_angle_fallback
                        
                        # calculate buffer radius (swath width from depth and swath angle)
                        buffer_radius = round(tan(radians(swath_angle/2)) * abs(pointXY_depth),0)
                        
                        # transform point from mercator zu UTM
                        fpoint_geom.transform(trans_merc2utm)
                        
                        # create buffer
                        buffer = fpoint_geom.buffer(buffer_radius,10)
                        
                        # transform buffer back to initial input CRS
                        buffer.transform(trans_utm2line)
                        
                        # store buffer in list
                        buffer_list.append(buffer)
                    
                    # check if any points in this segment have been sampled
                    if buffer_list == []:
                        continue
                    
                    # dissolve point buffers of line segment:
                    # dissolve all polygons based on line vertices into single feature
                    buffer_union = QgsGeometry().unaryUnion(buffer_list)
                    
                    # set fields and attributes:
                    # empty fields
                    buffer_fields = QgsFields()
                    
                    # loop through line feature fields
                    for field in feature.fields():
                        # and append all but the 'fid' field (if it exists)
                        if field.name() != 'fid':
                            buffer_fields.append(field)
                    
                    # append extra buffer fields (intial feature id, part id and segment id
                    for buffer_field in [feature_id_field, part_id_field, segment_id_field]:
                        buffer_fields.append(buffer_field)
                    
                    # if no input swath_angle field was selected on input, create one
                    if swath_angle_field == '':
                        swath_angle_field_name = 'mbes_swath_angle'
                        buffer_fields.append(QgsField(swath_angle_field_name,QVariant.Int,'Integer',len=5,prec=0))
                    
                    # initialize polygon feature
                    fpoly = QgsFeature(buffer_fields)
                    
                    # set attributes for polygon feature
                    for field in feature.fields():
                        # ignore 'fid' again
                        if field.name() != 'fid':
                            # set attribute from feature to buffer
                            fpoly.setAttribute(field.name(),feature.attribute(field.name()))
                    
                    # set addtional buffer fields
                    fpoly.setAttribute('feature_id', feature_id)
                    fpoly.setAttribute('part_id', part_id)
                    fpoly.setAttribute('segment_id', segment_id)
                    fpoly.setAttribute(swath_angle_field_name,swath_angle)
                    
                    # set geometry
                    fpoly.setGeometry(buffer_union)
                    
                    # store segment coverage polygon
                    if fpoly.hasGeometry() and fpoly.isValid():
                        buffer_union_list.append(fpoly)
            
            # set progess
            feedback.setProgress(int(feature_id * total))
        
        # if buffer_union_list is empty, no buffer features where created
        if buffer_union_list == []:
            raise Exception('No depth values could be sampled from the input raster!')
        
        # creating feature sink
        feedback.pushConsoleInfo(self.tr(f'Creating feature sink...'))
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context,
                                               buffer_fields, QgsWkbTypes.MultiPolygon, source.sourceCrs())
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
        
        # write coverage features to sink
        feedback.pushConsoleInfo(self.tr(f'Writing features...'))
        sink.addFeatures(buffer_union_list, QgsFeatureSink.FastInsert)
        
        # make variables accessible for post processing
        self.output = dest_id
        
        result = {self.OUTPUT : self.output}
        
        return result

    def postProcessAlgorithm(self, context, feedback):
        # check for error in processing algorithm
        #if self.output == None:
        #    return {}
        
        # get layer from source and context
        mbes_coverage_layer = QgsProcessingUtils.mapLayerFromString(self.output, context)
        
        # loading Cruise Tools Planning style from QML style file
        feedback.pushConsoleInfo(self.tr(f'Loading style...'))
        mbes_coverage_layer.loadNamedStyle(self.style_mbes_coverage)
        
        # writing style to GPKG (or else)
        style_name = 'Cruise Tools MBES Coverage'
        style_desc = 'MBES Coverage style for QGIS Symbology from Cruise Tools plugin'
        
        feedback.pushConsoleInfo(self.tr(f'Writing style to output...\n'))
        mbes_coverage_layer.saveStyleToDatabase(name=style_name, description=style_desc, useAsDefault=True, uiFileContent=None)
        
        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! MBES coverage has been estimated!\n'))
        
        result = {self.OUTPUT : self.output}
        
        return result

    def name(self):
        return 'estimatembescoverage'

    def icon(self):
        icon = QIcon(f'{self.plugin_dir}/icons/estimate_mbes_coverage.png')
        return icon
    
    def displayName(self):
        return self.tr('Estimate MBES Coverage')

    def group(self):
        return self.tr('Planning')

    def groupId(self):
        return 'planning'

    def tr(self, string):
        return QCoreApplication.translate('Processing',string)

    def shortHelpString(self):
        doc = f'{self.plugin_dir}/doc/estimate_mbes_coverage.help'
        if not os.path.exists(doc):
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return EstimateMBESCoverage()
