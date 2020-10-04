# -*- coding: utf-8 -*-
'''
/***************************************************************************
 CruiseTools
                                 A QGIS plugin
 Tool box for various GIS tasks for cruise planning, etc.
                              -------------------
        begin                : 2019-06-12
        git sha              : $Format:%H$
        copyright            : (C) 2019 by Simon Dreutter & Fynn Warnke
        email                : simon.dreutter@awi.de
                               fynn.warnke@awi.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
'''
from PyQt5.QtCore import *
from PyQt5.QtGui import *

# import some tools
from qgis.core import *
import math, processing

# import Cruise Tools modules
from .utils import *

def write_point_coordinates(layer):
    '''Write the point coordinates (LAT/LONG) of the SHP file into the attribute table'''
    # get CRS of input layer and create coordinate transformation
    crs_layer = layer.crs()
    trans = QgsCoordinateTransform(crs_layer, QgsCoordinateReferenceSystem('EPSG:4326'), QgsProject.instance())
    
    with edit(layer):
        # create fields for lat_DD and lon_DD coordinates in attribute table
        layer.addAttribute(QgsField("lat_DD",QVariant.Double,len=10,prec=6))
        layer.addAttribute(QgsField("lon_DD",QVariant.Double,len=10,prec=6))
        
        # create fields for lat_DDM and lon_DDM coordinates in attribute table
        layer.addAttribute(QgsField('lat_DDM',QVariant.String,len=10))
        layer.addAttribute(QgsField('lon_DDM',QVariant.String,len=10))
        
        # update attribute table fields
        layer.updateFields()
        
        # get all features
        features = get_features(layer,selected=False)
        
        for feature in features:
            # try catch to avoid error with MultiPoint layers
            try:
                # get geometry of feature
                geom = feature.geometry().asPoint()
                
                # transform geometry to EPSG:4326 CRS
                geom4326 = trans.transform(geom)
                
                # set geometry of each feature in the vector layer into seperate fields
                feature.setAttribute(feature.fieldNameIndex('lat_DD'), geom4326.y())
                feature.setAttribute(feature.fieldNameIndex('lon_DD'), geom4326.x())
                
                # convert DD to DDM
                lat_ddm, lon_ddm = dd2ddm(geom4326.y(), geom4326.x())
                
                # set DDM geometry of each feature
                feature.setAttribute(feature.fieldNameIndex('lat_DDM'), lat_ddm)
                feature.setAttribute(feature.fieldNameIndex('lon_DDM'), lon_ddm)
                
                # ipdate attribute table
                layer.updateFeature(feature)
            except TypeError:
                return 1, 'This didn\'t work. Is your layer a MULTIPOINT layer? If so, convert it to POINT, because only POINT layers are supported.' 
    
    return 0, None

#===============================================================================

def write_line_length(layer,m=True,nm=True):
    '''Write lengths of all features into attribute table'''
    # get CRS of input layer
    crs_layer = layer.crs()
    
    # set project ellipsoid (for measurements) to CRS ellipsoid
    ellipsoid = QgsProject.instance().crs().ellipsoidAcronym()
    
    # BACKUP: set project ellipsoid (for measurements) to LAYER CRS ellipsoid
    #ellipsoid = crs_layer.ellipsoidAcronym()
    
    # get transform context from project
    trans_context = QgsProject.instance().transformContext()
    
    # BACKUP: create transformContext from "scratch"
    #elps_crs = QgsCoordinateReferenceSystem()
    #elps_crs.createFromUserInput(ellipsoid)
    #trans_context = QgsCoordinateTransformContext()
    #trans_context.calculateDatumTransforms(crs_layer, elps_crs)
    
    # Initialize Distance calculator class with ellipsoid
    l = QgsDistanceArea()
    l.setSourceCrs(crs_layer,trans_context)
    l.setEllipsoid(ellipsoid)
    
    with edit(layer):
        # create fields for length_m and/or length_nm
        if m:
            layer.addAttribute(QgsField('length_m',QVariant.Double,len=15,prec=5))
        if nm:
            layer.addAttribute(QgsField('length_nm',QVariant.Double,len=15,prec=5))
        
        # update attribute table fields
        layer.updateFields()
        
        # get all features
        features = get_features(layer,selected=False)
        
        for feature in features:
            # get geometry of feature
            geom = feature.geometry()
            
            # measure feature length in meters
            len  = l.measureLength(geom)
            
            # set field values according to the calculated length
            if m:
                len_m = l.convertLengthMeasurement(len, QgsUnitTypes.DistanceMeters)
                len_m = round(len_m,2)
                feature.setAttribute(layer.fields().indexFromName('length_m'), len_m)
            if nm:
                len_nm = l.convertLengthMeasurement(len, QgsUnitTypes.DistanceNauticalMiles)
                len_nm = round(len_nm,5)
                feature.setAttribute(layer.fields().indexFromName('length_nm'), len_nm)
            
            # check if maxSpeed_kn exists
            f_idx_speed = layer.fields().indexFromName('maxSpeed_kn')
            f_idx_time = layer.fields().indexFromName('time_h')
            if (f_idx_speed != -1) and (f_idx_time != -1):
                # if yes, get value
                maxSpeed_kn = feature.attributes()[f_idx_speed]
                if maxSpeed_kn != None:
                    # if value not NULL, calculate time and write it to time_h field
                    len_nm = l.convertLengthMeasurement(len, QgsUnitTypes.DistanceNauticalMiles)
                    time_h = round(len_nm / maxSpeed_kn, 2)
                    feature.setAttribute(f_idx_time, time_h)
            
            # update attribute table
            layer.updateFeature(feature)
    
    return 0, None

#===============================================================================

def write_polygon_area(layer,m2=True,km2=True):
    '''Write area of all polygon features into attribute table'''
    # get CRS of input layer
    crs_layer = layer.crs()
    
    # set project ellipsoid (for measurements) to CRS ellipsoid
    ellipsoid = QgsProject.instance().crs().ellipsoidAcronym()
    
    # BACKUP: set project ellipsoid (for measurements) to LAYER CRS ellipsoid
    #ellipsoid = crs_layer.ellipsoidAcronym()
    
    # get transform context from project
    trans_context = QgsProject.instance().transformContext()
    
    # BACKUP: create transformContext from "scratch"
    #elps_crs = QgsCoordinateReferenceSystem()
    #elps_crs.createFromUserInput(ellipsoid)
    #trans_context = QgsCoordinateTransformContext()
    #trans_context.calculateDatumTransforms(crs_layer, elps_crs)
    
    # Initialize Area calculator class with ellipsoid
    l = QgsDistanceArea()
    l.setSourceCrs(crs_layer,trans_context)
    l.setEllipsoid(ellipsoid)
    
    with edit(layer):
        # create attribute table fields for specified units
        if m2:
            layer.addAttribute(QgsField('area_m2',QVariant.Double,len=15,prec=5))
        if km2:
            layer.addAttribute(QgsField('area_km2',QVariant.Double,len=15,prec=5))
            
        layer.updateFields()
        
        # get all features
        features = get_features(layer,selected=False)
        
        for feature in features:
            # get geometry
            geom = feature.geometry()
            
            # area in SQUARE METERS
            area = l.measureArea(geom)
            
            # set field values according to calculated AREA
            if m2:
                area_m2 = l.convertAreaMeasurement(area, QgsUnitTypes.AreaSquareMeters)
                feature.setAttribute(layer.fields().indexFromName('area_m2'), area_m2)
            if km2:
                area_km2 = l.convertAreaMeasurement(area, QgsUnitTypes.AreaSquareKilometers)
                feature.setAttribute(layer.fields().indexFromName('area_km2'), area_km2)
            
            # update attribute table
            layer.updateFeature(feature)
    
    return 0, None

#===============================================================================

def swap_vectors(layer,selected=True):
    '''Swap line vector direction'''
    with edit(layer):
        # get (selected) features
        features = get_features(layer,selected=selected)
        
        # reverse line direction for each (selected) feature 
        for feature in features:
            geom = feature.geometry()
            if geom.isMultipart():
                mls = QgsMultiLineString()
                for line in geom.asGeometryCollection():
                    mls.addGeometry(line.constGet().reversed())
                    newgeom = QgsGeometry(mls)
                layer.changeGeometry(feature.id(),newgeom)
            else:
                newgeom = QgsGeometry(geom.constGet().reversed())
                layer.changeGeometry(feature.id(),newgeom)
    
    return 0, None
