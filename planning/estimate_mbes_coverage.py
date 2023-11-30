import os
from math import tan, radians, degrees

from qgis.core import (
    QgsProject,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
    QgsDistanceArea,
    QgsFeature,
    QgsFeatureSink,
    QgsField,
    QgsFields,
    QgsPointXY,
    QgsGeometry,
    QgsGeometryUtils,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterFeatureSink,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterBand,
    QgsProcessingParameterEnum,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterDefinition,
    QgsProcessingUtils,
    QgsProcessingException,
    QgsWkbTypes
)

from qgis.PyQt.QtCore import QCoreApplication, QVariant
from PyQt5.QtGui import QIcon

from .planning import Planning
from .. import utils

def get_swath_angle(feature, swath_angle_field, swath_angle_fallback):
    """Get swath angle for feature.

    Parameters
    ----------
    feature : QgsFeature
        QgsFeature with attributes
    swath_angle_field : str
        Name of swath angle field
    swath_angle_fallback : int or float
        Swath angle fallback value

    Returns
    -------
    swath_angle : int or float
        Swath angle from field or fallback

    """
    # create depth-dependant buffer:
    # check if swath_angle field is selected
    if swath_angle_field != '':
        # get value from field
        swath_angle_field_value = feature.attribute(swath_angle_field)
        # check if value is set (not NULL)
        if not swath_angle_field_value:
            # if NULL, set fallback
            swath_angle = swath_angle_fallback
        else:
            # othervise take value from field
            swath_angle = swath_angle_field_value
    else:
        swath_angle = swath_angle_fallback
    
    return swath_angle


def get_inner_angle(vertices: list, idx: int):
    """Calculate inner angle of vertex at `idx` in `vertices` list.

    Parameters
    ----------
    vertices : list[QgsPoint]
        List of vertices (of LineString or Polygon outline).
    idx : int
        Vertex index.

    Returns
    -------
    a : float
        Inner angle of vertex at index `idx`.
    
    """
    a1 = degrees(
        QgsGeometryUtils.lineAngle(
            vertices[idx - 1].x(), vertices[idx - 1].y(),
            vertices[idx].x(), vertices[idx].y(),
        )
    )
    a2 = degrees(
        QgsGeometryUtils.lineAngle(
            vertices[idx].x(), vertices[idx].y(),
            vertices[idx + 1].x(), vertices[idx + 1].y(),
        )
    )
    
    if (a1 > a2) and (a1 > (a2 + 180)):
        a = 540 - a1 + a2
    elif (a1 > a2):
        a = 180 - a1 + a2
    elif (a1 < a2) and ((a1 + 180) > a2):
        a = 180 + a2 - a1
    elif (a1 < a2):
        a = a2 - a1 - 180
    
    a = 360 - a
    a = (a + 360) % 360
    
    return a

class EstimateMBESCoverage(QgsProcessingAlgorithm, Planning):
    """Estimate MBES Coverage."""

    # Processing parameters
    # inputs:
    INPUT_LINE = 'INPUT_LINE'
    INPUT_RASTER = 'INPUT_RASTER'
    BAND = 'BAND'
    DISSOLVE_BUFFER = 'DISSOLVE_BUFFER'
    SWATH_ANGLE_MODE = 'SWATH_ANGLE_MODE'
    SWATH_ANGLE_FIELD = 'SWATH_ANGLE_FIELD'
    SWATH_ANGLE = 'SWATH_ANGLE'
    SWATH_ANGLE_FIELD_PORT = 'SWATH_ANGLE_FIELD_PORT'
    SWATH_ANGLE_PORT = 'SWATH_ANGLE_PORT'
    SWATH_ANGLE_FIELD_STARBOARD = 'SWATH_ANGLE_FIELD_STARBOARD'
    SWATH_ANGLE_STARBOARD = 'SWATH_ANGLE_STARBOARD'
    # outputs:
    OUTPUT = 'OUTPUT'

    def __init__(self):
        """Initialize CreatePlanningFile."""
        super(EstimateMBESCoverage, self).__init__()
        
        self.swath_angle_modi = {
            0: 'Total angle',
            1: 'Port/Starboard angles'
        }
        
        # style files for mbes coverage layers
        self.style_mbes_coverage = ':/plugins/cruisetools/styles/style_mbes_coverage.qml'
        self.style_mbes_coverage_vertices = ':/plugins/cruisetools/styles/style_mbes_coverage_vertices.qml'
        
        # distance for line densifier
        self.vertex_distance = 50  # m
        # buffer settings
        self.buffer_segments = 10
        self.buffer_join_style = QgsGeometry.JoinStyleRound
        
        # initialize default configuration
        self.initConfig()

    def initConfig(self):
        """Get default values from CruiseToolsConfig."""
        self.swath_angle_mode = self.config.getint(self.module, 'swath_angle_mode')
        self.swath_angle = self.config.getint(self.module, 'swath_angle')
        self.swath_angle_port = self.config.getint(self.module, 'swath_angle_port')
        self.swath_angle_stb = self.config.getint(self.module, 'swath_angle_stb')
        # self.line_layer_name = self.config.getint(self.module, 'line_layer')
        self.raster_layer_name = self.config.getint(self.module, 'raster_layer')

    def initAlgorithm(self, config=None):  # noqa
        # line_layers = [lyr for lyr in QgsProject.instance().mapLayers().values() if lyr.type() == 0]
        # line_layer_names = [line.name() for line in line_layers]
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                name=self.INPUT_LINE,
                description=self.tr('Input MBES line planning layer'),
                types=[QgsProcessing.TypeVectorLine],
                defaultValue=None,
                # (
                #     self.line_layer_name
                #     if self.line_layer_name in line_layer_names
                #     else None
                # ),
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.DISSOLVE_BUFFER,
                description=self.tr('Dissolve line segment buffers (per feature)'),
                optional=False,
                defaultValue=True
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.SWATH_ANGLE_MODE,
                description=self.tr('Swath opening angle mode'),
                options=list(self.swath_angle_modi.values()),
                defaultValue=0,  # TODO: self.swath_angle_mode,
                optional=False,
                allowMultiple=False)
        )
        self.parameterDefinition(self.SWATH_ANGLE_MODE).setMetadata({
            'widget_wrapper': {
                'useCheckBoxes': True,
                'columns': 2,
            }
        })
        self.parameterDefinition(self.SWATH_ANGLE_MODE).setFlags(
            QgsProcessingParameterDefinition.FlagAdvanced
        )
        
        self.addParameter(
            QgsProcessingParameterField(
                name=self.SWATH_ANGLE_FIELD,
                description=self.tr('Swath angle field'),
                defaultValue='mbes_swath_angle',
                parentLayerParameterName=self.INPUT_LINE,
                type=QgsProcessingParameterField.Numeric,
                allowMultiple=False,
                optional=True)
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                name=self.SWATH_ANGLE,
                description=self.tr('Swath angle (fallback)'),
                type=QgsProcessingParameterNumber.Integer,
                optional=True,
                defaultValue=self.swath_angle,
                minValue=10,
                maxValue=160)
        )
        params = [
            # PORT
            QgsProcessingParameterField(
                name=self.SWATH_ANGLE_FIELD_PORT,
                description=self.tr('Port angle field'),
                defaultValue='mbes_swath_angle_port',
                parentLayerParameterName=self.INPUT_LINE,
                type=QgsProcessingParameterField.Numeric,
                allowMultiple=False,
                optional=True
            ),
            QgsProcessingParameterNumber(
                name=self.SWATH_ANGLE_PORT,
                description=self.tr('Port angle (fallback)'),
                type=QgsProcessingParameterNumber.Integer,
                optional=True,
                defaultValue=self.swath_angle_port,
                minValue=5,
                maxValue=80
            ),
            # STARBOARD
            QgsProcessingParameterField(
                name=self.SWATH_ANGLE_FIELD_STARBOARD,
                description=self.tr('Starboard angle field'),
                defaultValue='mbes_swath_angle_stb',
                parentLayerParameterName=self.INPUT_LINE,
                type=QgsProcessingParameterField.Numeric,
                allowMultiple=False,
                optional=True
            ),
            QgsProcessingParameterNumber(
                name=self.SWATH_ANGLE_STARBOARD,
                description=self.tr('Starboard angle (fallback)'),
                type=QgsProcessingParameterNumber.Integer,
                optional=True,
                defaultValue=self.swath_angle_stb,
                minValue=5,
                maxValue=80
            )
        ]
        for param in params:
            param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
            self.addParameter(param)
        
        raster_layers = [lyr for lyr in QgsProject.instance().mapLayers().values() if lyr.type() == 1]
        raster_layer_names = [r.name() for r in raster_layers]
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                name=self.INPUT_RASTER,
                description=self.tr('Input bathymetry raster layer'),
                defaultValue=(
                    self.raster_layer_name
                    if self.raster_layer_name in raster_layer_names
                    else None
                ),  # None
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBand(
                name=self.BAND,
                description=self.tr('Band number'),
                defaultValue=1,
                parentLayerParameterName=self.INPUT_RASTER,
                optional=False,
                allowMultiple=False)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.OUTPUT,
                description=self.tr('MBES coverage'),
                type=QgsProcessing.TypeVectorPolygon,
                defaultValue=None,
                optional=False,
                createByDefault=True)
        )

    def processAlgorithm(self, parameters, context, feedback):  # noqa
        # get input variables
        source = self.parameterAsSource(parameters, self.INPUT_LINE, context)
        
        dissolve_buffer = self.parameterAsBoolean(parameters, self.DISSOLVE_BUFFER, context)  # TODO
        
        swath_angle_mode = self.parameterAsInt(parameters, self.SWATH_ANGLE_MODE, context)
        
        # total opening angle
        swath_angle_field = self.parameterAsString(parameters, self.SWATH_ANGLE_FIELD, context)
        swath_angle_fallback = self.parameterAsInt(parameters, self.SWATH_ANGLE, context)
        
        # port/starboard angles
        swath_angle_field_port = self.parameterAsString(parameters, self.SWATH_ANGLE_FIELD_PORT, context)
        swath_angle_port_fallback = self.parameterAsInt(parameters, self.SWATH_ANGLE_PORT, context)
        swath_angle_field_stb = self.parameterAsString(parameters, self.SWATH_ANGLE_FIELD_STARBOARD, context)
        swath_angle_stb_fallback = self.parameterAsInt(parameters, self.SWATH_ANGLE_STARBOARD, context)
        
        raster_layer = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        band_number = self.parameterAsInt(parameters, self.BAND, context)
        
        # copy of the field name for later
        swath_angle_field_name = swath_angle_field
        swath_angle_field_port_name = swath_angle_field_port
        swath_angle_field_stb_name = swath_angle_field_stb
        
        # set new default values in config
        feedback.pushConsoleInfo(self.tr('Storing new default settings in config...'))
        # self.config.set(self.module, 'line_layer', source.sourceName())
        self.config.set(self.module, 'swath_angle_mode', swath_angle_mode)
        self.config.set(self.module, 'swath_angle', swath_angle_fallback)
        self.config.set(self.module, 'swath_angle_port', swath_angle_port_fallback)
        self.config.set(self.module, 'swath_angle_stb', swath_angle_stb_fallback)
        self.config.set(self.module, 'raster_layer', raster_layer.name())
        
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
        # trans_line2raster = QgsCoordinateTransform(crs_line, crs_raster, transform_context)
        crs_geo = QgsCoordinateReferenceSystem('EPSG:4326')
        trans_line2geo = QgsCoordinateTransform(crs_line, crs_geo, transform_context)
        
        # initialize distance tool
        da = QgsDistanceArea()
        da.setSourceCrs(crs_mercator, transform_context)
        da.setEllipsoid(crs_mercator.ellipsoidAcronym())
        
        # list for polygons features (unioned buffer)
        buffer_union_features = []
        
        # get (selected) features
        features = source.getFeatures()
        
        # feedback
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        
        # loop through features
        feedback.pushConsoleInfo(self.tr('Densifying line features...'))
        feedback.pushConsoleInfo(self.tr('Extracting vertices...'))
        feedback.pushConsoleInfo(self.tr('Sampling values...'))
        feedback.pushConsoleInfo(self.tr('Computing depth dependent buffers...'))
        feedback.pushConsoleInfo(self.tr('Unionizing output features...'))
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
                # list for unioned buffer
                list_buffer_union_segments = []
                
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
                    segment_geom = QgsGeometry.fromPolylineXY([vertices_t[segment_id], vertices_t[segment_id + 1]])
                    
                    # measure ellipsoidal distance between start and end vertex
                    segment_length = da.measureLength(segment_geom)
                    
                    # calculate number of extra vertices to insert
                    extra_vertices = int(segment_length // self.vertex_distance)
                    
                    # create additional vertices along line segment
                    segment_geom_dense = segment_geom.densifyByCount(extra_vertices - 1)
                    segment_vertices = list(segment_geom_dense.vertices())
                    segment_vertices_cnt = len(segment_vertices)
                    
                    # initialize additional fields
                    feature_id_field = QgsField('feature_id', QVariant.Int, 'Integer', len=5, prec=0)
                    part_id_field = QgsField('part_id', QVariant.Int, 'Integer', len=5, prec=0)
                    segment_id_field = QgsField('segment_id', QVariant.Int, 'Integer', len=5, prec=0)
                    
                    # list for segment buffers
                    buffer_list = []
                    
                    # loop over all vertices of line segment
                    for i in range(segment_vertices_cnt - 1):
                        
                        pnt_start = QgsPointXY(segment_vertices[i])
                        pnt_end = QgsPointXY(segment_vertices[i + 1])
                        
                        # [BUFFER] create geometry
                        geom_line = QgsGeometry.fromPolylineXY([pnt_start, pnt_end])
                        # geom_point = QgsGeometry.fromPointXY(pnt_end)
                        
                        # [BUFFER] transform geometry from World Mercator to local UTM zone
                        geom_line.transform(trans_merc2utm)
                        # geom_point.transform(trans_merc2utm)
                        
                        # [RASTER] transform point to raster CRS
                        pnt_start_rasterCRS = trans_merc2raster.transform(pnt_start)
                        pnt_end_rasterCRS = trans_merc2raster.transform(pnt_end)
                        
                        # [RASTER]  sample raster at point locations
                        pnt_start_depth, error_check_start = raster_layer.dataProvider().sample(pnt_start_rasterCRS, band_number)
                        pnt_end_depth, error_check_end = raster_layer.dataProvider().sample(pnt_end_rasterCRS, band_number)
                        pointXY_depth = (pnt_start_depth + pnt_end_depth) / 2
                        
                        # check if valid depth was sampled, otherwise skip point
                        if error_check_start is False or error_check_end is False:
                            continue
                        
                        # get swath angle
                        if swath_angle_mode == 0:
                            swath_angle = get_swath_angle(feature, swath_angle_field, swath_angle_fallback)
                            
                            # calculate buffer radius (swath width from depth and swath angle)
                            buffer_radius = round(tan(radians(swath_angle / 2)) * abs(pointXY_depth), 0)
                            
                            # create buffer
                            buffer = geom_line.buffer(
                                buffer_radius, self.buffer_segments,  # FIXME: endCapStyle=QgsGeometry.CapFlat
                            )
                        
                        elif swath_angle_mode == 1:
                            swath_angle_port = get_swath_angle(feature, swath_angle_field_port, swath_angle_port_fallback)  # swath_angle_port_fallback
                            swath_angle_stb = get_swath_angle(feature, swath_angle_field_stb, swath_angle_stb_fallback)
                        
                            # calculate buffer radius (swath width from depth and swath angle)
                            buffer_dist_port = round(tan(radians(swath_angle_port)) * abs(pointXY_depth), 0)
                            buffer_dist_stb = round(tan(radians(swath_angle_stb)) * abs(pointXY_depth), 0)
                            
                            # create unioned buffer from port/starboard buffers
                            buffer_port = geom_line.singleSidedBuffer(
                                buffer_dist_port, self.buffer_segments, side=QgsGeometry.SideLeft, joinStyle=self.buffer_join_style
                            )
                            buffer_stb = geom_line.singleSidedBuffer(
                                buffer_dist_stb, self.buffer_segments, side=QgsGeometry.SideRight, joinStyle=self.buffer_join_style
                            )
                            # single buffer
                            buffer = QgsGeometry.unaryUnion([buffer_port, buffer_stb])  # OPTIMIZE: .simplify(1)

                        # transform buffer back to initial input CRS
                        buffer.transform(trans_utm2line)
                        
                        # store buffer in list
                        buffer_list.append(buffer)
                    
                    # check if any points in this segment have been sampled
                    if buffer_list == []:
                        continue
                    
                    # dissolve point buffers of line segment:
                    # dissolve all polygons based on line vertices into single feature
                    buffer_union = QgsGeometry.unaryUnion(buffer_list).convexHull()
                    list_buffer_union_segments.append(buffer_union)
                    
                    # [MODE] Create QgsFeature ONLY if required for output
                    if not dissolve_buffer:
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
                        if swath_angle_mode == 0 and swath_angle_field == '':
                            swath_angle_field_name = 'mbes_swath_angle'
                            buffer_fields.append(QgsField(swath_angle_field_name, QVariant.Int, 'Integer', len=5, prec=0))
                        elif swath_angle_mode == 1:
                            if swath_angle_field_port == '':
                                swath_angle_field_port_name = 'mbes_swath_angle_port'
                                buffer_fields.append(QgsField(swath_angle_field_port_name, QVariant.Int, 'Integer', len=5, prec=0))
                            if swath_angle_field_stb == '':
                                swath_angle_field_stb_name = 'mbes_swath_angle_stb'
                                buffer_fields.append(QgsField(swath_angle_field_stb_name, QVariant.Int, 'Integer', len=5, prec=0))
                        
                        # initialize polygon feature
                        fpoly = QgsFeature(buffer_fields)
                        
                        # set attributes for polygon feature
                        for field in feature.fields():
                            # ignore 'fid' again
                            if field.name() != 'fid':
                                # set attribute from feature to buffer
                                fpoly.setAttribute(field.name(), feature.attribute(field.name()))
                        
                        # set addtional buffer fields
                        fpoly.setAttribute('feature_id', feature_id)
                        fpoly.setAttribute('part_id', part_id)
                        fpoly.setAttribute('segment_id', segment_id)
                        if swath_angle_mode == 0:
                            fpoly.setAttribute(swath_angle_field_name, swath_angle)
                        elif swath_angle_mode == 1:
                            fpoly.setAttribute(swath_angle_field_port_name, swath_angle_port)
                            fpoly.setAttribute(swath_angle_field_stb_name, swath_angle_stb)
                        
                        # set geometry
                        fpoly.setGeometry(buffer_union)
                        
                        # store segment coverage polygon
                        if fpoly.hasGeometry() and fpoly.isValid():
                            buffer_union_features.append(fpoly)
                            
                # [DISSOLVE]
                if dissolve_buffer:
                    # create coverage poylgon for all segments of part (aka feature for non MultiLineString)
                    buffer_part = QgsGeometry.unaryUnion(list_buffer_union_segments)
                    
                    # remove buffer polygon vertices with `inner_angle` > threshold --> "infill corners"
                    if swath_angle_mode == 1:
                        inner_angle = 270
                        # extract vertices
                        buffer_vertices = list(buffer_part.vertices())
                        buffer_vertices_cnt = len(buffer_vertices)
                        
                        # create LineString in UTM coordinates (slightly buffered)
                        vertices_UTM = [QgsPointXY(v) for v in vertices_t]
                        line_part_buffer = QgsGeometry.fromPolylineXY(vertices_UTM).buffer(1, self.buffer_segments)
                        
                        # get vertex indices to remove
                        indices_to_remove = [
                            i for i in range(1, buffer_vertices_cnt - 1)
                            if (get_inner_angle(buffer_vertices, i) > inner_angle)
                            and (line_part_buffer.contains(QgsPointXY(buffer_vertices[i])))
                        ]
                        
                        # create MBES converage polygon WITHOUT vertices to remove
                        buffer_part = QgsGeometry.fromPolygonXY([[
                            QgsPointXY(v) for idx, v in enumerate(buffer_vertices) if idx not in indices_to_remove
                        ]])
                    
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
                    if swath_angle_mode == 0 and swath_angle_field == '':
                        swath_angle_field_name = 'mbes_swath_angle'
                        buffer_fields.append(QgsField(swath_angle_field_name, QVariant.Int, 'Integer', len=5, prec=0))
                    elif swath_angle_mode == 1:
                        if swath_angle_field_port == '':
                            swath_angle_field_port_name = 'mbes_swath_angle_port'
                            buffer_fields.append(QgsField(swath_angle_field_port_name, QVariant.Int, 'Integer', len=5, prec=0))
                        if swath_angle_field_stb == '':
                            swath_angle_field_stb_name = 'mbes_swath_angle_stb'
                            buffer_fields.append(QgsField(swath_angle_field_stb_name, QVariant.Int, 'Integer', len=5, prec=0))
                    
                    # initialize polygon feature
                    fpoly = QgsFeature(buffer_fields)
                    
                    # set attributes for polygon feature
                    for field in feature.fields():
                        # ignore 'fid' again
                        if field.name() != 'fid':
                            # set attribute from feature to buffer
                            fpoly.setAttribute(field.name(), feature.attribute(field.name()))
                    
                    # set addtional buffer fields
                    fpoly.setAttribute('feature_id', feature_id)
                    fpoly.setAttribute('part_id', part_id)
                    fpoly.setAttribute('segment_id', 999)
                    if swath_angle_mode == 0:
                        fpoly.setAttribute(swath_angle_field_name, swath_angle)
                    elif swath_angle_mode == 1:
                        fpoly.setAttribute(swath_angle_field_port_name, swath_angle_port)
                        fpoly.setAttribute(swath_angle_field_stb_name, swath_angle_stb)
                    
                    # set geometry
                    fpoly.setGeometry(buffer_part)
                    
                    # store segment coverage polygon
                    if fpoly.hasGeometry() and fpoly.isValid():
                        buffer_union_features.append(fpoly)
                
            # set progess
            feedback.setProgress(int(feature_id * total))
        
        # if buffer_union_features is empty, no buffer features where created
        if buffer_union_features == []:
            raise Exception('No depth values could be sampled from the input raster!')
        
        # creating feature sink
        feedback.pushConsoleInfo(self.tr('Creating feature sink...'))
        (sink, dest_id) = self.parameterAsSink(
            parameters, self.OUTPUT, context, buffer_fields, QgsWkbTypes.MultiPolygon, source.sourceCrs()
        )
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))
        
        # write coverage features to sink
        feedback.pushConsoleInfo(self.tr('Writing features...'))
        sink.addFeatures(buffer_union_features, QgsFeatureSink.FastInsert)
        
        # make variables accessible for post processing
        self.output = dest_id
        
        result = {self.OUTPUT : self.output}
        
        return result

    def postProcessAlgorithm(self, context, feedback):  # noqa
        # check for error in processing algorithm
        #if self.output == None:
        #    return {}
        
        # get layer from source and context
        mbes_coverage_layer = QgsProcessingUtils.mapLayerFromString(self.output, context)
        
        # loading Cruise Tools Planning style from QML style file
        feedback.pushConsoleInfo(self.tr('Loading style...'))
        mbes_coverage_layer.loadNamedStyle(self.style_mbes_coverage)
        
        # writing style to GPKG (or else)
        style_name = 'Cruise Tools MBES Coverage'
        style_desc = 'MBES Coverage style for QGIS Symbology from Cruise Tools plugin'
        
        feedback.pushConsoleInfo(self.tr('Writing style to output...\n'))
        mbes_coverage_layer.saveStyleToDatabase(name=style_name, description=style_desc, useAsDefault=True, uiFileContent=None)
        
        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! MBES coverage has been estimated!\n'))
        
        result = {self.OUTPUT : self.output}
        
        return result

    def name(self):  # noqa
        return 'estimatembescoverage'

    def icon(self):  # noqa
        icon = QIcon(f'{self.plugin_dir}/icons/estimate_mbes_coverage.png')
        return icon
    
    def displayName(self):  # noqa
        return self.tr('Estimate MBES Coverage')

    def group(self):  # noqa
        return self.tr('Planning')

    def groupId(self):  # noqa
        return 'planning'

    def tr(self, string):  # noqa
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):  # noqa
        doc = f'{self.plugin_dir}/doc/estimate_mbes_coverage.help'
        if not os.path.exists(doc):
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):  # noqa
        return EstimateMBESCoverage()
