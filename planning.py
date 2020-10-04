# -*- coding: utf-8 -*-
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# import some tools
from qgis.core import *
from math import tan, radians, floor
import os
import processing

# import Cruise Tools modules
from .utils import *
from .config import *
from .vector import *

style_planning_lines = ':/plugins/cruisetools/styles/style_planning_lines.qml'
style_planning_points = ':/plugins/cruisetools/styles/style_planning_points.qml'
style_planning_lines_vertices = ':/plugins/cruisetools/styles/style_planning_lines_vertices.qml'
style_mbes_coverage = ':/plugins/cruisetools/styles/style_mbes_coverage.qml'
style_mbes_coverage_vertices = ':/plugins/cruisetools/styles/style_mbes_coverage_vertices.qml'

def create_point_planning_file():
    '''Create point planning file'''
    # set output file
    title = 'Create Point Planning File'
    path = os.path.join(QgsProject.instance().homePath(),'point_planning')
    filter = 'GeoPackage (*.gpkg);;ESRI Shapefile (*.shp)'
    error, output = select_output_file(title,path,filter)
    if error:
        return error, 'No output file selected!'
    
    base_path,base_name,ext = get_info_from_path(output)
    
    # get output file driver (GPKG or ESRI Shapefile)
    driver = get_driver_from_path(output)
    
    # test if a driver could be identified
    if driver is None:
        return 1, 'File driver could not be identified!'
    
    # create temporary memory vector layer
    uri = 'Point?crs=epsg:4326&field=name:string(50)&field=notes:string(0)&index=yes'
    tmp_layer = QgsVectorLayer(uri, base_name, 'memory')
    
    # write empty layer to file
    error, result = QgsVectorFileWriter.writeAsVectorFormat(tmp_layer, output, 'utf-8', driverName=driver)
    if error != QgsVectorFileWriter.NoError:
        return 1, 'File could not be written!'
    
    # dereference tmp_layer
    tmp_layer = None
    
    # load points from file
    planning_layer = QgsVectorLayer(output, base_name, 'ogr')
    
    # load planning style from style file
    planning_layer.loadNamedStyle(style_planning_points)
    
    # add to canvas
    QgsProject.instance().addMapLayer(planning_layer)
    
    return 0, output

#===============================================================================

def create_line_planning_file():
    '''Create line planning file'''
    # set output file
    title = 'Create Line Planning File'
    path = os.path.join(QgsProject.instance().homePath(),'line_planning')
    filter = 'GeoPackage (*.gpkg);;ESRI Shapefile (*.shp)'
    error, output = select_output_file(title,path,filter)
    if error:
        return error, 'No output file selected!'
    
    base_path,base_name,ext = get_info_from_path(output)
    
    # get output file driver (GPKG or ESRI Shapefile)
    driver = get_driver_from_path(output)
    
    # test if a driver could be identified
    if driver is None:
        return 1, 'File driver could not be identified!'
    
    # create temporary memory vector layer
    uri = 'Linestring?crs=epsg:4326&field=name:string(50)&field=turnRadius_nm:double(4,2)&field=maxSpeed_kn:double(4,2)&field=time_h:double(4,2)&field=notes:string(0)&index=yes'
    tmp_layer = QgsVectorLayer(uri, base_name, 'memory')
    
    # write empty layer to file
    error, result = QgsVectorFileWriter.writeAsVectorFormat(tmp_layer, output, 'utf-8', driverName=driver)
    if error != QgsVectorFileWriter.NoError:
        return 1, 'File could not be written!'
    
    # dereference tmp_layer
    tmp_layer = None
    
    # load lines from file
    planning_layer = QgsVectorLayer(output, base_name, 'ogr')
    
    # load planning style from style file
    planning_layer.loadNamedStyle(style_planning_lines)
    
    # add to canvas
    QgsProject.instance().addMapLayer(planning_layer)
    
    return 0, output

#===============================================================================

def planning_lines_to_vertices(line_layer):
    '''Convert planning line files to vertices for coordinate export'''
    # set output file
    name = line_layer.name()
    title = 'Create Vertices From Lines'
    path = os.path.join(QgsProject.instance().homePath(),'{}_vertices'.format(name))
    filter = 'GeoPackage (*.gpkg);;ESRI Shapefile (*.shp)'
    error, output = select_output_file(title,path,filter)
    if error:
        return error, 'No output file selected!'
    
    base_path,base_name,ext = get_info_from_path(output)
    
    # get output file driver (GPKG or ESRI Shapefile)
    driver = get_driver_from_path(output)
    
    # test if a driver could be identified
    if driver is None:
        return 1, 'File driver could not be identified!'
    
    tmp_layer = lines_to_vertices(line_layer,base_name)
    
    # write memory layer to disk
    error, result = QgsVectorFileWriter.writeAsVectorFormat(tmp_layer, output, 'utf-8', driverName=driver)
    if error != QgsVectorFileWriter.NoError:
        return 1, 'File could not be written!'
    
    # dereference tmp_layer
    tmp_layer = None
    
    # load lines from file
    vertex_layer = QgsVectorLayer(output, base_name, 'ogr')
    
    # add corrdinates to attributes
    write_point_coordinates(vertex_layer)
    
    # load planning style from style file
    vertex_layer.loadNamedStyle(style_planning_lines_vertices)
    
    # add to canvas
    QgsProject.instance().addMapLayer(vertex_layer)
    
    return 0, output

#===============================================================================

def lines_to_vertices(line_layer,name):
    '''Convert lines to vertices (helper function)'''
    # create temporary memory vector layer
    vertex_layer = QgsVectorLayer('Point?crs=epsg:4326', name, 'memory')
    provider = vertex_layer.dataProvider()
    
    # initialize attribute fields
    provider.addAttributes(line_layer.fields())
    provider.deleteAttributes([0])
    vertex_layer.updateFields()
    
    # get (selected) features
    features = get_features(line_layer,selected=True)
    
    with edit(vertex_layer):
        # get geometry and attributes of all line features
        for vertice in features:
            # initialize feature
            feature = QgsFeature(vertex_layer.fields())
            
            # get line attributes
            attrs = vertice.attributes()
            
            # write copied attributes
            for i, attrField in enumerate(line_layer.fields().names()[1:]):
                feature.setAttribute(attrField, attrs[i+1])
            
            # get line geometry (start and end points)
            geom = vertice.geometry().asPolyline()
            start_point = geom[0]
            end_point = geom[-1]
            
            for g in geom:
                feature.setGeometry(QgsGeometry.fromPointXY(g))
                provider.addFeatures([feature])
            
            vertex_layer.updateFeature(feature)
            vertex_layer.updateFields()
    
    return vertex_layer

#===============================================================================

def get_UTM_zone(lat, lon):
    """Get appropriated UTM zone EPSG ID for line feature"""   
    utm_band = str((floor((lon + 180) / 6 ) % 60) + 1)
    if len(utm_band) == 1:
        utm_band = '0'+utm_band
    if lat >= 0:
        epsg_code = '326' + utm_band
    else:
        epsg_code = '327' + utm_band
    return QgsCoordinateReferenceSystem(f'EPSG:{epsg_code}')

def extend_uri_with_fields(uri, fields):
    for field in fields:
        uri = f'{uri}&field={field.name()}:{field.typeName()}'
    return uri

def transform_vertices(vertices, transformer):
    transformed_list = []
    for v in vertices:
        v_trans = transformer.transform(v)
        transformed_list.append(v_trans)
    return transformed_list

def extend_attribute_fields(fields, attributes):
    """Extend list of feature attributes with NULL value according to given field amount"""
    return attributes + [NULL] * (fields.count() - len(attributes))

def create_scratch_layer(feature_list:list, epsg_id:int, name:str, fields, to_canvas=True):
    # get GeometryType as string
    geom_type = QgsWkbTypes().geometryDisplayString(feature_list[0].geometry().type())
    if geom_type == 'Polygon':
        suffix = 'MBES_coverage'
    elif geom_type == 'Point':
        suffix = 'MBES_vertices'
    elif geom_type == 'Line':
        geom_type = 'Linestring'
        suffix = 'line'
    
    uri_base = f'{geom_type.lower()}?crs=epsg:{epsg_id}'
    uri = extend_uri_with_fields(uri_base, fields)
    layer_name = f'{name}_{suffix}'
    layer = QgsVectorLayer(uri, layer_name, 'memory')
    # add features to VectorLayer (returns True if successful)
    success, _ = layer.dataProvider().addFeatures(feature_list)
    
    old_layer = QgsProject.instance().mapLayersByName(layer_name)
    if len(old_layer) != 0:
        QgsProject.instance().removeMapLayers([old_layer[0].id()])
    
    if to_canvas:
        added = QgsProject.instance().addMapLayer(layer)
        if added == None:
            print('WARNING: Layer was not added to canvas!')
    
    return layer

def calculate_mbes_coverage(line_layer, raster_layer, raster_band, SWATH_ANGLE):
    # get line planning layer
    line_name = line_layer.name()
    crs_line = line_layer.crs()
    
    # get DEM to sample
    raster_name = raster_layer.name()
    crs_raster = raster_layer.crs()
    
    # initialize crs transformer
    transformContext = QgsProject.instance().transformContext()
    # CRS transformation to "WGS84/World Mercator" for MBES coverage operations
    crs_mercator = QgsCoordinateReferenceSystem('EPSG:3395')
    trans_line2merc = QgsCoordinateTransform(crs_line, crs_mercator, transformContext)
    # CRS transformation to raster layer CRS for depth sampling
    trans_merc2raster = QgsCoordinateTransform(crs_mercator, crs_raster, transformContext)
    trans_line2raster = QgsCoordinateTransform(crs_line, crs_raster, transformContext)
    crs_geo = QgsCoordinateReferenceSystem('EPSG:4326')
    trans_line2geo = QgsCoordinateTransform(crs_line, crs_geo, transformContext)
    
    # initialize distance tool
    l = QgsDistanceArea()
    l.setSourceCrs(crs_mercator, transformContext)
    l.setEllipsoid(crs_mercator.ellipsoidAcronym())

    point_list = []
    buffer_union_list = []
    
    # get (selected) features
    features = get_features(line_layer,selected=True)
    
    for feature_id, f in enumerate(features):
        # get feature geometry
        g = f.geometry()
        
        # check for LineString geometry
        if QgsWkbTypes.isSingleType(g.wkbType()):
            # get list of vertices
            vertices_list = g.asPolyline()
            vertices_list = [vertices_list]
        # check for MultiLineString geometry
        elif QgsWkbTypes.isMultiType(g.wkbType()):
            # get list of list of vertices per multiline part
            vertices_list = g.asMultiPolyline()
        
        for part_id, vertices in enumerate(vertices_list): 
            # transform vertices CRS to "WGS 84 / World Mercator"
            vertices_t = transform_vertices(vertices, trans_line2merc)
            
            # get UTM zone of feature for buffering
            centroid = g.centroid()
            centroid_point = centroid.asPoint()
            lat, lon = centroid_point.y(), centroid_point.x()
            crs_utm = get_UTM_zone(lat, lon)
            trans_merc2utm = QgsCoordinateTransform(crs_mercator, crs_utm, transformContext)
            trans_utm2line = QgsCoordinateTransform(crs_utm, crs_line, transformContext)
            
            # split line into segments
            for segment_id in range(len(vertices_t) - 1):
                # ===== (1) DENSIFY LINE VERTICES =====
                # create new Polyline geometry for line segment
                segment_geom = QgsGeometry.fromPolylineXY([vertices_t[segment_id], vertices_t[segment_id+1]])
                # measure ellipsoidal distance between start and end vertex
                segment_length = l.measureLength(segment_geom)
                # calculate number of extra vertices to insert
                vertex_distance = 50 #m
                extra_vertices = int(segment_length // vertex_distance)
                # create additional vertices along line segment
                geom_dense = segment_geom.densifyByCount(extra_vertices - 1)
                
                # ===== (2) CREATE POINTS AND BUFFER POLYGONS =====
                # initialize QgsFeature fields and attributes for point layer
                # get fields from input feature
                point_fields = f.fields()
                # initialize additional fields
                feature_id_field = QgsField('feature_id',QVariant.Int,'Integer',len=5,prec=0)
                part_id_field = QgsField('part_id',QVariant.Int,'Integer',len=5,prec=0)
                segment_id_field = QgsField('segment_id',QVariant.Int,'Integer',len=5,prec=0)
                point_id_field = QgsField('point_id',QVariant.Int,'Integer',len=5,prec=0)
                depth_field = QgsField('depth_m_sampled',QVariant.Double,'Real',len=9,prec=2,comment='Sampled raster depth')
                swath_angle_field = QgsField('swath_angle_deg',QVariant.Int,'Integer',len=5,prec=0)
                footprint_field = QgsField('coverage_m',QVariant.Int,'Integer',len=8,prec=0)
                # add additional fields
                for field in [feature_id_field, part_id_field, segment_id_field, point_id_field, \
                              depth_field, swath_angle_field, footprint_field]:
                    point_fields.append(field)
                
                # list for segment buffers
                buffer_list = []
                
                # loop over all vertices of line segment
                for i, vertex in enumerate(geom_dense.vertices()):
                    # === CREATE POINT FEATURE ===
                    # initialize feature and set geometry
                    fpoint = QgsFeature()
                    fpoint.setGeometry(vertex)
                    
                    # === SAMPLE BATHYMETRY GRID ===
                    # get point geometry (as QgsPointXY)
                    fpoint_geom = fpoint.geometry()
                    pointXY = fpoint_geom.asPoint()
                    # transform point to raster CRS
                    pointXY_raster = trans_merc2raster.transform(pointXY) #trans_line2raster.transform(pointXY)
                    # sample raster at point location
                    pointXY_depth, error_check = raster_layer.dataProvider().sample(pointXY_raster, 1)
                    # check if valid depth was sampled, otherwise skip point
                    if error_check == False:
                        print('[WARNING]   Point is outside raster area or wrong band number specified!')
                        continue
                    
                    # === SET POINT ATTRIBUTES ===
                    # set feature fields 
                    fpoint.setFields(point_fields)  
                    # set feature attributes (extended according to feature fields) 
                    fpoint.setAttributes( extend_attribute_fields(point_fields, f.attributes()) )
                    fpoint.setAttribute('feature_id', feature_id)
                    fpoint.setAttribute('part_id', part_id)
                    fpoint.setAttribute('segment_id', segment_id)
                    fpoint.setAttribute('point_id', i)
                    fpoint.setAttribute('depth_m_sampled', pointXY_depth)
                    fpoint.setAttribute('swath_angle_deg', SWATH_ANGLE)
                    
                    # === CREATE DEPTH-DEPENDANT BUFFER ===
                    buffer_radius = round(tan(radians(SWATH_ANGLE/2)) * abs(pointXY_depth),0)
                    fpoint_geom.transform(trans_merc2utm)
                    buffer = fpoint_geom.buffer(buffer_radius,10)
                    buffer.transform(trans_utm2line)
                    # add coverage size to attributes
                    fpoint.setAttribute('coverage_m', buffer_radius * 2)
                    
                    # === TRANSFORMATION TO ORIGINAL LINE CRS ===
                    # transform Point & set new feature geometry
                    fpoint_geom.transform(trans_utm2line)
                    fpoint.setGeometry(fpoint_geom)
                    
                    # === STORE POINT AND BUFFER ===
                    point_list.append(fpoint)
                    buffer_list.append(buffer)
                # check if any points in this segment have been sampled
                if point_list == []:
                    continue
                
                # ===== (3) DISSOLVE POINT BUFFERS OF LINE SEGMENT =====
                #  dissolve all polygons based on line vertices into single feature
                buffer_union = QgsGeometry().unaryUnion(buffer_list)
                
                # initialize Polygon feature
                fpoly = QgsFeature()
                # set fields and attributes
                buffer_fields = f.fields()
                for buffer_field in [feature_id_field, part_id_field, segment_id_field, swath_angle_field]:
                    buffer_fields.append(buffer_field)
                fpoly.setFields(buffer_fields)
                fpoly.setAttributes( extend_attribute_fields(buffer_fields, f.attributes()) )
                fpoly.setAttribute('feature_id', feature_id)
                fpoly.setAttribute('part_id', part_id)
                fpoly.setAttribute('segment_id', segment_id)
                fpoly.setAttribute('swath_angle_deg',SWATH_ANGLE)
                # set geometry
                fpoly.setGeometry(buffer_union)
                
                # === STORE SEGMENT COVERAGE POLYGON ===
                buffer_union_list.append(fpoly)
    # check if any points have been sampled properly
    if point_list == []:
        return 1, 'No depth values could be sampled from the input raster!'
    
    point_layer = create_scratch_layer(point_list, crs_line.postgisSrid(), line_name, point_fields, to_canvas=True)
    point_layer.loadNamedStyle(style_mbes_coverage_vertices)
    node = QgsProject.instance().layerTreeRoot().findLayer(point_layer.id())
    if node:
        node.setItemVisibilityChecked(False)
    
    coverage_layer = create_scratch_layer(buffer_union_list, crs_line.postgisSrid(), line_name, buffer_fields, to_canvas=True)
    coverage_layer.loadNamedStyle(style_mbes_coverage)
    
    return 0, None

#===============================================================================

def export_points_to_bridge(point_layer):
    '''Export planning points for vessel ECDIS transfer'''
    # get vesser from config
    vessel = get_vessel_config()
    
    # get CRS of input layer and create coordinate transformation
    crs = point_layer.crs()
    trans = QgsCoordinateTransform(crs, QgsCoordinateReferenceSystem('EPSG:4326'), QgsProject.instance())
    
    # get (selected) features
    features = get_features(point_layer,selected=True)
        
    # empty list for features
    table =[]
    
    # create dict holding all features with fieldnames and geometry
    for i,feature in enumerate(features):
        feature_fields = feature.fields().names()
        feature_attributes = feature.attributes()
        # add minimum of required fields if they don't exist
        if not 'fid' in feature_fields:
            feature_fields.append('fid')
            feature_attributes.append(i+1)
        if not 'name' in feature_fields:
            feature_fields.append('name')
            feature_attributes.append('')
        # zip lists to dict
        feature_dict = dict(zip(feature_fields,feature_attributes))
        # get geometry of feature
        geom = feature.geometry().asPoint()
        # transform geometry to EPSG:4326 CRS
        geom4326 = trans.transform(geom)
        feature_dict['lat_DD'] = geom4326.y()
        feature_dict['lon_DD'] = geom4326.x()
        # convert DD to DDM
        #lat_ddm, lon_ddm = dd2ddm(geom4326.y(), geom4326.x())
        lat_ddm, lon_ddm = dd2ddm(geom4326.y(), geom4326.x())
        feature_dict['lat_DDM'] = lat_ddm
        feature_dict['lon_DDM'] = lon_ddm
        
        table.append(feature_dict)
    
    # select export function from vessel
    if vessel == 'default':
        error, result = export_csv(table,point_layer.name())
    elif vessel == 'RV Sonne':
        error, result = export_SAM_route(table,vessel,point_layer.name())
    elif vessel == 'RV Maria S. Merian':
        error, result = export_SAM_route(table,vessel,point_layer.name())
    elif vessel == 'RV Polarstern':
        error, result = export_csv(table,point_layer.name())
    
    return error, result

def export_lines_to_bridge(line_layer):
    '''Export planning lines for vessel ECDIS transfer'''
    # get layer with line vertices
    vertex_layer = lines_to_vertices(line_layer,line_layer.name())
    
    # export points
    error, result = export_points_to_bridge(vertex_layer)
    
    # dereference vertex_layer
    vertex_layer = None
    
    return error, result

def export_csv(table,name):
    '''Export table as Comma Separated Value [CSV]'''
    # set output file
    title = 'Export Points to CSV'
    path = os.path.join(QgsProject.instance().homePath(),name)
    filter = 'Comma Separated Value [CSV] (*.csv)'
    error, output = select_output_file(title,path,filter)
    if error:
        return error, 'No output file selected!'
    
    base_path,base_name,ext = get_info_from_path(output)
    
    # header line
    key_list = ['"' + x + '"' for x in table[0].keys()]
    #header = ','.join(table[0].keys())
    header = ','.join(key_list)
    
    # write table to file
    with open(output, 'w',encoding='ansi') as f:
        # write header
        f.write(header + '\n')
        # write fields and geometry from features
        for feature in table:
            line = []
            for field in header.split(','):
                line.append(feature[field.replace('"','')])
            line = ['"' + str(x).replace('NULL','') + '"' for x in line]
            f.write(','.join(line) + '\n')
    
    return 0, output

def export_SAM_route(table,vessel,name):
    '''Export table as SAM Route to bridge Comma Separated Value [CSV]'''
    # set output file
    title = 'Export Points to SAM Route'
    path = os.path.join(QgsProject.instance().homePath(),name)
    filter = 'Comma Separated Value [CSV] (*.csv)'
    error, output = select_output_file(title,path,filter)
    if error:
        return error, 'No output file selected!'
    
    base_path,base_name,ext = get_info_from_path(output)
    
    with open(output,'w',encoding='ansi') as f:
        f.write('"Name","Latitude [°]","Longitude [°]","Turn Radius [NM]","Max. Speed [kn]","XTD [m]","Sailmode","Additional Notes"\n')
        for feature in table:
            # concat name and fid for 'Name' column
            if feature['name'] == '':
                name_out = feature['fid']
            else:
                name_out = str(feature['fid']) + '_' + feature['name']
            for i in ['turnRadius_nm','maxSpeed_kn','notes']:
                if not i in feature:
                    feature[i] = ''
            # compose line
            line = '"{}","{}","{}","{}","{}","","","{}"\n'.format(name_out,
                                                    round(feature['lat_DD'],6),
                                                    round(feature['lon_DD'],6),
                                                    feature['turnRadius_nm'],
                                                    feature['maxSpeed_kn'],
                                                    feature['notes'])
            # replace empty fields ('NULL') with nothing ('')
            line = line.replace('NULL','')
            # write line to file
            f.write(line)
    
    return 0, output
