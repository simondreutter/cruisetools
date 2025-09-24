import os
from math import tan, radians, degrees
import numpy as np

from qgis.core import QgsCoordinateTransform
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsDistanceArea
from qgis.core import QgsFeature
from qgis.core import QgsFeatureSink
from qgis.core import QgsField
from qgis.core import QgsFields
from qgis.core import QgsPointXY
from qgis.core import QgsGeometry
from qgis.core import QgsGeometryUtils
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingException
from qgis.core import QgsProcessingParameterBand
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsProcessingParameterDefinition
from qgis.core import QgsProcessingParameterEnum
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterField
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingUtils
from qgis.core import QgsProject
from qgis.core import QgsWkbTypes

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
            # otherwise take value from field
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
    DENSIFY_MODE = 'DENSIFY_MODE'
    DENSIFY_VALUE = 'DENSIFY_VALUE'
    # outputs:
    OUTPUT = 'OUTPUT'

    def __init__(self):
        """Initialize CreatePlanningFile."""
        super(EstimateMBESCoverage, self).__init__()

        self.swath_angle_modi = {
            0: 'Total angle',
            1: 'Port/Starboard angles'
        }
        
        self.densify_modes = ['Number of points', 'Distance']

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
        self.dissolve_buffer = self.config.getint(self.module, 'dissolve_buffer')
        self.swath_angle_mode = self.config.getint(self.module, 'swath_angle_mode')
        self.swath_angle = self.config.getint(self.module, 'swath_angle')
        self.swath_angle_port = self.config.getint(self.module, 'swath_angle_port')
        self.swath_angle_stb = self.config.getint(self.module, 'swath_angle_stb')
        # self.line_layer_name = self.config.getint(self.module, 'line_layer')
        self.raster_layer_name = self.config.getint(self.module, 'raster_layer')

    def initAlgorithm(self, config=None):  # noqa
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
                defaultValue=self.dissolve_buffer)
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.SWATH_ANGLE_MODE,
                description=self.tr('Swath opening angle mode'),
                options=list(self.swath_angle_modi.values()),
                defaultValue=self.swath_angle_mode,
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
                maxValue=80)
        ]
        for param in params:
            param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
            self.addParameter(param)
        
        # DENSIFY OPTIONS
        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.DENSIFY_MODE,
                description=self.tr('Densify mode (defines output coverage resolution)'),
                options=self.densify_modes,
                defaultValue=self.densify_modes[0],
                optional=False,
                allowMultiple=False)
        )
        self.parameterDefinition(self.DENSIFY_MODE).setMetadata({
            'widget_wrapper': {
                'useCheckBoxes': True,
                'columns': 2,
            }
        })
        self.parameterDefinition(self.DENSIFY_MODE).setFlags(
            QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                    name=self.DENSIFY_VALUE,
                    description=self.tr('Number of points [#] OR Distance [m]'),
                    type=QgsProcessingParameterNumber.Integer,
                    defaultValue=100,
                    optional=True,
                    minValue=0)
        )
        self.parameterDefinition(self.DENSIFY_VALUE).setFlags(
            QgsProcessingParameterDefinition.FlagAdvanced
        )
        
        # RASTER
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
                ),
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

        dissolve_buffer = self.parameterAsBoolean(parameters, self.DISSOLVE_BUFFER, context)

        swath_angle_mode = self.parameterAsInt(parameters, self.SWATH_ANGLE_MODE, context)

        # total opening angle
        swath_angle_field = self.parameterAsString(parameters, self.SWATH_ANGLE_FIELD, context)
        swath_angle_fallback = self.parameterAsInt(parameters, self.SWATH_ANGLE, context)

        # port/starboard angles
        swath_angle_field_port = self.parameterAsString(parameters, self.SWATH_ANGLE_FIELD_PORT, context)
        swath_angle_port_fallback = self.parameterAsInt(parameters, self.SWATH_ANGLE_PORT, context)
        swath_angle_field_stb = self.parameterAsString(parameters, self.SWATH_ANGLE_FIELD_STARBOARD, context)
        swath_angle_stb_fallback = self.parameterAsInt(parameters, self.SWATH_ANGLE_STARBOARD, context)
        
        # densify mode
        densify_mode = self.densify_modes[self.parameterAsInt(parameters, self.DENSIFY_MODE, context)]
        densify_value = self.parameterAsInt(parameters, self.DENSIFY_VALUE, context)
        
        raster_layer = self.parameterAsRasterLayer(parameters, self.INPUT_RASTER, context)
        band_number = self.parameterAsInt(parameters, self.BAND, context)

        # copy of the field name for later
        swath_angle_field_name = swath_angle_field
        swath_angle_field_port_name = swath_angle_field_port
        swath_angle_field_stb_name = swath_angle_field_stb

        # set new default values in config
        feedback.pushConsoleInfo(self.tr('Storing new default settings in config...'))
        # self.config.set(self.module, 'line_layer', source.sourceName())
        self.config.set(self.module, 'dissolve_buffer', dissolve_buffer)
        self.config.set(self.module, 'swath_angle_mode', swath_angle_mode)
        self.config.set(self.module, 'swath_angle', swath_angle_fallback)
        self.config.set(self.module, 'swath_angle_port', swath_angle_port_fallback)
        self.config.set(self.module, 'swath_angle_stb', swath_angle_stb_fallback)
        self.config.set(self.module, 'raster_layer', raster_layer.name())

        # get CRS
        crs_line = source.sourceCrs()
        crs_raster = raster_layer.crs()

        # get project transform_context
        transform_context = context.transformContext()

        # CRS transformation to "WGS84/World Mercator" for MBES coverage operations
        crs_mercator = QgsCoordinateReferenceSystem('EPSG:3395')
        trans_line2merc = QgsCoordinateTransform(crs_line, crs_mercator, transform_context)

        # CRS transformation to geographic projection (for UTM zone estimate)
        # trans_merc2raster = QgsCoordinateTransform(crs_mercator, crs_raster, transform_context)
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

            # transform from line CRS to "WGS 84 / World Mercator" (EPSG:3395)
            # -> same projection as navigation software on most research vessel 
            feature_geom_epsg3395 = QgsGeometry(feature_geom)  # deep copy
            feature_geom_epsg3395.transform(trans_line2merc)

            # check for LineString geometry
            if QgsWkbTypes.isSingleType(feature_geom.wkbType()):
                # get list of vertices
                vertices_list = [feature_geom.asPolyline()]
                vertices_list_epsg3395 = [feature_geom_epsg3395.asPolyline()]

            # check for MultiLineString geometry
            elif QgsWkbTypes.isMultiType(feature_geom.wkbType()):
                # get list of lists of vertices per multiline part
                vertices_list = feature_geom.asMultiPolyline()
                vertices_list_epsg3395 = feature_geom_epsg3395.asMultiPolyline()

            for part_id, (vertices, vertices_t) in enumerate(zip(vertices_list, vertices_list_epsg3395)):
                # list for unioned buffer
                list_buffer_union_segments = []

                # get centroid as point for UTM zone selection
                centroid = feature_geom.centroid()
                centroid_point = centroid.asPoint()

                # check if centroid needs to be transformed to get x/y in lon/lat
                if not crs_line.isGeographic():
                    centroid_point = trans_line2geo.transform(centroid_point)

                # get UTM zone of feature for buffering
                lat, lon = centroid_point.y(), centroid_point.x()
                crs_utm = self.get_utm_zone(lat, lon)

                # create back and forth transformations for later
                trans_merc2utm = QgsCoordinateTransform(crs_mercator, crs_utm, transform_context)
                trans_utm2line = QgsCoordinateTransform(crs_utm, crs_line, transform_context)
                trans_utm2raster = QgsCoordinateTransform(crs_utm, crs_raster, transform_context)

                # split line into segments
                for segment_id in range(len(vertices_t) - 1):
                    # ===== (1) DENSIFY LINE VERTICES =====
                    # create new Polyline geometry for line segment
                    segment_geom = QgsGeometry.fromPolylineXY([vertices_t[segment_id], vertices_t[segment_id + 1]])

                    # measure ellipsoidal distance between start and end vertex
                    segment_length = da.measureLength(segment_geom)

                    # calculate number of extra vertices to insert
                    if densify_mode == self.densify_modes[0]:  # number of points
                        extra_vertices = densify_value
                    elif densify_mode == self.densify_modes[1]:  # distance
                        extra_vertices = int(segment_length // densify_value) - 2
                        extra_vertices = 0 if extra_vertices <= 0 else extra_vertices

                    # Densify input line segment
                    segment_geom_dense = segment_geom.densifyByCount(extra_vertices)
                    # Transform segment from World Mercator (EPSG:3395) to local UTM zone
                    segment_geom_dense_utm = QgsGeometry(segment_geom_dense)  # deep copy
                    check = segment_geom_dense_utm.transform(trans_merc2utm)
                    if check != 0:
                        raise Exception('CRS transformation failed')
                    # Transform segment from local UTM zone to raster CRS
                    segment_geom_dense_raster = QgsGeometry(segment_geom_dense_utm)  # deep copy
                    check = segment_geom_dense_raster.transform(trans_utm2raster)
                    if check != 0:
                        raise Exception('CRS transformation failed')
                        
                    # Extract segment vertices
                    segment_vertices_utm = segment_geom_dense_utm.asPolyline()
                    segment_vertices_raster = segment_geom_dense_raster.asPolyline()

                    # initialize additional fields
                    feature_id_field = QgsField('feature_id', QVariant.Int, 'Integer', len=5, prec=0)
                    part_id_field = QgsField('part_id', QVariant.Int, 'Integer', len=5, prec=0)
                    segment_id_field = QgsField('segment_id', QVariant.Int, 'Integer', len=5, prec=0)
                    
                    # init list of outer beams
                    beams_stbd = []
                    beams_port = []
                    
                    bearing = 0
                    
                    # loop over all vertices of line segment
                    for i, pt in enumerate(segment_vertices_utm):
                        # Calculate bearing (in degrees) using local UTM projection
                        bearing = (
                            degrees(da.bearing(pt, segment_vertices_utm[i + 1])) % 360
                            if i < len(segment_vertices_utm) - 1 else bearing  # use previous bearing for last vertex
                        )
                        
                        # Sample raster at densified point along line segement (in raster CRS)
                        pt_depth, check = raster_layer.dataProvider().sample(segment_vertices_raster[i], band_number)
                        if not check:
                            # print(f'[WARN] No depth found. Skipping point < {i} >')
                            continue
                        
                        # Get swath angle
                        if swath_angle_mode == 0:
                            swath_angle = get_swath_angle(feature, swath_angle_field, swath_angle_fallback)
                            swath_angle_port = swath_angle_stb = swath_angle // 2
                        elif swath_angle_mode == 1:
                            swath_angle_port = get_swath_angle(feature, swath_angle_field_port, swath_angle_port_fallback)
                            swath_angle_stb = get_swath_angle(feature, swath_angle_field_stb, swath_angle_stb_fallback)
                        
                        # Calculate horizontal distance (flat surface)
                        dist_stbd_flat = abs(tan(radians(swath_angle_stb)) * pt_depth)
                        dist_port_flat = abs(tan(radians(swath_angle_port)) * pt_depth)
                        
                        # Project starboard/port outer beams
                        pt_stbd_flat = pt.project(dist_stbd_flat, (bearing + 90) % 360)
                        pt_port_flat = pt.project(dist_port_flat, (bearing - 90) % 360)
                        
                        # Create swath line geometry (flat)
                        swath_flat = QgsGeometry.fromPolylineXY([pt_port_flat, pt_stbd_flat])
                        
                        # Sample bathymetry along perpendicular line (swath)
                        FACTOR_EXTEND = 1.5  # 50% extension to account for seafloor dipping away from ship
                        dist_stbd_extend = dist_stbd_flat * FACTOR_EXTEND
                        dist_port_extend = dist_port_flat * FACTOR_EXTEND
                        n_swath_densify = 100
    
                        # Extend swath (horizontal) by 50% to each side
                        swath_flat_extend = swath_flat.extendLine(dist_port_extend, dist_stbd_extend)
                        swath_flat_extend_raster = QgsGeometry(swath_flat_extend)  # deep copy
                        swath_flat_extend_raster.transform(trans_utm2raster)
                        vertices_swath_flat = swath_flat_extend_raster.densifyByCount(n_swath_densify).asPolyline()
                        swath_flat_depths = np.array([
                            raster_layer.dataProvider().sample(v, band_number)[0] for v in vertices_swath_flat
                        ])
                        if len(swath_flat_depths) == 0:
                            raise Exception('No depths could be sampled from the input raster!')
                        
                        # Interpolate NaNs in sampled depths
                        idx_nans = np.isnan(swath_flat_depths)
                        x = np.arange(len(swath_flat_depths))
                        # Note: np.interp replaces outer NaNs with the last valid value
                        swath_flat_depths[idx_nans] = np.interp(x[idx_nans], x[~idx_nans], swath_flat_depths[~idx_nans])
                        
                        # Calculate intersection of outer beams with bathymetry (sampled depths)
                        # using an arbitrary reference system (x: distance along swath, y: depth)
                        # Init beams
                        beam_stbd = QgsGeometry.fromPolylineXY([QgsPointXY(0, 0), QgsPointXY(dist_stbd_flat, pt_depth)])
                        beam_port = QgsGeometry.fromPolylineXY([QgsPointXY(0, 0), QgsPointXY(-dist_port_flat, pt_depth)])
                        
                        # Extend beams
                        beam_stbd = beam_stbd.extendLine(0, beam_stbd.length() * FACTOR_EXTEND)
                        beam_port = beam_port.extendLine(0, beam_port.length() * FACTOR_EXTEND)
                        
                        # Init bathymetric profile (extended)
                        xx = np.linspace(-(dist_port_flat + dist_port_extend), dist_stbd_flat + dist_stbd_extend, n_swath_densify, endpoint=True)
                        swath_bathy = QgsGeometry.fromPolylineXY([QgsPointXY(x, y) for x, y in zip(xx, swath_flat_depths)])
                        
                        # Get outer beam positions
                        # STARBOARD
                        intersection_stbd = beam_stbd.intersection(swath_bathy)
                        if not intersection_stbd.isEmpty():
                            # Project expected outer beam position
                            if intersection_stbd.isMultipart():
                                # print(f'[WARN] Multiple stbd intersections found for point < {i} > (using nearest point)')
                                dist_stbd = abs(list(intersection_stbd.vertices())[0].x())
                            else:
                                dist_stbd = abs(intersection_stbd.asPoint().x())
                            pt_stbd = pt.project(dist_stbd, (bearing + 90) % 360)
                            pt_stbd_src = trans_utm2line.transform(QgsPointXY(pt_stbd))
                            beams_stbd.append(pt_stbd_src)
                        # else:
                            # print(f'[WARN] No starboard intersection found for point < {i} >')
                        
                        # PORT
                        intersection_port = beam_port.intersection(swath_bathy)
                        if not intersection_port.isEmpty():
                            # Project expected outer beam position
                            if intersection_port.isMultipart():
                                # print(f'[WARN] Multiple port intersections found for point < {i} >! Using nearest point.')
                                dist_port = abs(list(intersection_port.vertices())[0].x())
                            else:
                                dist_port = abs(intersection_port.asPoint().x())
                            pt_port = pt.project(dist_port, (bearing - 90) % 360)
                            pt_port_src = trans_utm2line.transform(QgsPointXY(pt_port))
                            beams_port.append(pt_port_src)
                        # else:
                            # print(f'[WARN] No port intersection found for point < {i} >!')
                    
                    if len(beams_stbd) == 0 or len(beams_port) == 0:
                        # print(f'[WARN]  Found no valid depths along segment < {segment_id} >!')
                        continue

                    # Create coverage polygon for line segement
                    buffer_union = QgsGeometry.fromPolygonXY([beams_stbd + beams_port[::-1]])
                    list_buffer_union_segments.append(buffer_union)

                    # [MODE] Create QgsFeature ONLY if required for output
                    if not dissolve_buffer:
                        # init fields
                        buffer_fields = QgsFields()

                        # loop through line feature fields
                        for field in feature.fields():
                            # and append all but the 'fid' field (if it exists)
                            if field.name() != 'fid':
                                buffer_fields.append(field)

                        # append extra buffer fields (initial feature id, part id and segment id
                        for buffer_field in [feature_id_field, part_id_field, segment_id_field]:
                            buffer_fields.append(buffer_field)

                        # if no input swath_angle field was selected on input, create one
                        if swath_angle_mode == 0 and swath_angle_field == '':
                            swath_angle_field_name = 'mbes_swath_angle'
                            buffer_fields.append(
                                QgsField(swath_angle_field_name, QVariant.Int, 'Integer', len=5, prec=0))
                        elif swath_angle_mode == 1:
                            if swath_angle_field_port == '':
                                swath_angle_field_port_name = 'mbes_swath_angle_port'
                                buffer_fields.append(
                                    QgsField(swath_angle_field_port_name, QVariant.Int, 'Integer', len=5, prec=0))
                            if swath_angle_field_stb == '':
                                swath_angle_field_stb_name = 'mbes_swath_angle_stb'
                                buffer_fields.append(
                                    QgsField(swath_angle_field_stb_name, QVariant.Int, 'Integer', len=5, prec=0))

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
                if dissolve_buffer and len(list_buffer_union_segments) > 0:
                    # create coverage poylgon for all segments of part (aka feature for non MultiLineString)
                    buffer_part = QgsGeometry.unaryUnion(list_buffer_union_segments)
                    
                    # remove input line vertices from coverage polygon --> "infill corners"
                    v_buffer = buffer_part.asPolygon()[0]  # outer ring
                    v_filt = [v for v in v_buffer if v not in vertices]
                    
                    buffer_part = QgsGeometry.fromPolygonXY([v_filt])
                    
                    # init fields
                    buffer_fields = QgsFields()

                    # loop through line feature fields
                    for field in feature.fields():
                        # and append all but the 'fid' field (if it exists)
                        if field.name() != 'fid':
                            buffer_fields.append(field)

                    # append extra buffer fields (initial feature id, part id and segment id
                    for buffer_field in [feature_id_field, part_id_field, segment_id_field]:
                        buffer_fields.append(buffer_field)

                    # if no input swath_angle field was selected on input, create one
                    if swath_angle_mode == 0 and swath_angle_field == '':
                        swath_angle_field_name = 'mbes_swath_angle'
                        buffer_fields.append(QgsField(swath_angle_field_name, QVariant.Int, 'Integer', len=5, prec=0))
                    elif swath_angle_mode == 1:
                        if swath_angle_field_port == '':
                            swath_angle_field_port_name = 'mbes_swath_angle_port'
                            buffer_fields.append(
                                QgsField(swath_angle_field_port_name, QVariant.Int, 'Integer', len=5, prec=0))
                        if swath_angle_field_stb == '':
                            swath_angle_field_stb_name = 'mbes_swath_angle_stb'
                            buffer_fields.append(
                                QgsField(swath_angle_field_stb_name, QVariant.Int, 'Integer', len=5, prec=0))

                    # initialize polygon feature
                    fpoly = QgsFeature(buffer_fields)

                    # set attributes for polygon feature
                    for field in feature.fields():
                        # ignore 'fid' again
                        if field.name() != 'fid':
                            # set attribute from feature to buffer
                            fpoly.setAttribute(field.name(), feature.attribute(field.name()))

                    # set additional buffer fields
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

            # set progress
            feedback.setProgress(int(feature_id * total))

        # if buffer_union_features is empty, no buffer features where created
        if buffer_union_features == []:
            raise Exception('No depth values could be sampled from the input raster! Please check input line and raster.')

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

        # make variables accessible for post-processing
        self.output = dest_id

        result = {self.OUTPUT: self.output}

        return result
    
    def postProcessAlgorithm(self, context, feedback):  # noqa
        
        # get layer from source and context
        mbes_coverage_layer = QgsProcessingUtils.mapLayerFromString(self.output, context)

        # loading Cruise Tools Planning style from QML style file
        feedback.pushConsoleInfo(self.tr('Loading style...'))
        mbes_coverage_layer.loadNamedStyle(self.style_mbes_coverage)

        # writing style to GPKG (or else)
        style_name = 'Cruise Tools MBES Coverage'
        style_desc = 'MBES Coverage style for QGIS Symbology from Cruise Tools plugin'

        feedback.pushConsoleInfo(self.tr('Writing style to output...\n'))
        mbes_coverage_layer.saveStyleToDatabase(name=style_name, description=style_desc, useAsDefault=True,
                                                uiFileContent=None)

        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! MBES coverage has been estimated!\n'))

        result = {self.OUTPUT: self.output}

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
