import os

from qgis.core import (
    edit,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsDistanceArea,
    QgsFeatureRequest,
    QgsField,
    QgsGeometry,
    QgsMultiLineString,
    QgsUnitTypes,
    QgsWkbTypes
)

from qgis.PyQt.QtCore import QVariant

from .. import config
from .. import utils

class Vector(object):
    """Base class for vector modules."""

    def __init__(self):
        """Initialize Vector."""
        self.module = 'VECTOR'
        self.config = config.CruiseToolsConfig()
        self.plugin_dir = f'{os.path.dirname(__file__)}/..'

    def get_features(self, layer, selected=True):
        """Get features from vector layer.

        Parameters
        ----------
        layer : QgsVectorLayer
            input vector layer
        selected : boolean
            return just selected or all features (Default value = True)

        Returns
        -------
        features : QgsFeature list/iterator
            selectes features

        """
        # check if any features are selected and only use those in that case
        if selected is False:
            features = layer.getFeatures()
        elif layer.selectedFeatureCount() == 0:
            features = layer.getFeatures()
        elif layer.selectedFeatureCount() > 0:
            features = layer.getSelectedFeatures()
        
        return features
    
    def select_features(self, layer, filter=''):
        """Select features from layer by filter expression.

        Parameters
        ----------
        layer : QgsVectorLayer
            input vector layer
        filter : str
            filter expression (Default value = '')

        Returns
        -------
        selection : QgsFeature list/iterator
            selectes features

        """
        request = QgsFeatureRequest().setFilterExpression(filter)
        selection = layer.getFeatures(request)
        return selection

    def delete_features(self, layer, features):
        """Delete features from layer.

        Parameters
        ----------
        layer : QgsVectorLayer
            input vector layer
        features : QgsFeature list/iterator
            list of features

        """
        with edit(layer):
            for feature in features:
                layer.deleteFeature(feature.id())
        return

    def delete_fields_by_prefix(self, layer, prefix):
        """Delete fields from layer attributes with matching prefix.

        Parameters
        ----------
        layer : QgsVectorLayer
            input vector layer
        prefix : str or list
            prefix for fields to delete (string or list of strings)

        """
        if isinstance(prefix, str):
            prefix_list = [prefix]
        else:
            prefix_list = prefix
        delete_fields = []
        for field in layer.fields():
            for field_prefix in prefix_list:
                if field.name().startswith(field_prefix):
                    field_idx = layer.fields().indexFromName(field.name())
                    delete_fields.append(field_idx)
        layer.dataProvider().deleteAttributes(delete_fields)
        layer.updateFields()
        
        return

    def write_point_coordinates(self, layer, transform_context, latlon_DD=False, latlon_DDM=False, xy=False, crs_xy=None):
        """Write the point coordinates (LAT/LONG) of the SHP file into the attribute table.

        Parameters
        ----------
        layer : QgsVectorLayer
            input point vector layer
        transform_context : QgsCoordinateTransformContext
            transform context for coordinate transformation
        latlon_DD : boolean
            write Lat Lon Decimal Degrees (Default value = False)
        latlon_DDM : boolean
            write Lat Lon Degrees Decimal Minutes (Default value = False)
        xy : boolean
            write XY (Default value = False)
        crs_xy : QgsCoordinateReferenceSystem or None
            output CRS for XY coordinate attribute (Default value = None)

        Returns
        -------
        error : boolean
            0/1 - no error/error
        result : str or None
            output or error msg if error == 1

        """
        # if no coordinates shall be written, return
        if latlon_DD == latlon_DDM == xy == False:
            return 1, 'No coordinate types selected, no attributes created!\n'
        
        # geometry type
        geom_type = QgsWkbTypes.geometryType(layer.wkbType())
        multi_type = QgsWkbTypes.isMultiType(layer.wkbType())
        if (geom_type != 0) or multi_type:
            return 1, 'This didn\'t work. Is your layer a MULTIPOINT layer? If so, convert it to POINT, because only POINT layers are supported.\n'
        
        # if output CRS for XY is not valid, set to layer CRS
        if (crs_xy is None) or (crs_xy is not None and not crs_xy.isValid()):
            crs_xy = layer.crs()
        
        # set some field names
        lat_DD_field = 'lat_DD'
        lon_DD_field = 'lon_DD'
        
        lat_DDM_field = 'lat_DDM'
        lon_DDM_field = 'lon_DDM'
        
        xy_suffix = f'{crs_xy.authid().replace("EPSG:", "epsg")}'
        x_field = f'x_{xy_suffix}'
        y_field = f'y_{xy_suffix}'
        
        # get CRS of input layer and create coordinate transformation to EPSG:4326
        crs_layer = layer.crs()
        trans4326 = QgsCoordinateTransform(crs_layer, QgsCoordinateReferenceSystem('EPSG:4326'), transform_context)
        transXY = QgsCoordinateTransform(crs_layer, crs_xy, transform_context)
        
        # with edit(layer):
            
        if not layer.isEditable():
            layer.startEditing()
            
        # delete fields previously created by Cruise Tools
        prefix_list = ['lat_D', 'lon_D', 'x_epsg', 'y_epsg']
        self.delete_fields_by_prefix(layer, prefix_list)
        
        if latlon_DD:
            # create fields for lat_DD and lon_DD coordinates in attribute table
            layer.addAttribute(QgsField(lat_DD_field, QVariant.Double, len=10, prec=6))
            layer.addAttribute(QgsField(lon_DD_field, QVariant.Double, len=10, prec=6))
        
        if latlon_DDM:
            # create fields for lat_DDM and lon_DDM coordinates in attribute table
            layer.addAttribute(QgsField(lat_DDM_field, QVariant.String, len=11))
            layer.addAttribute(QgsField(lon_DDM_field, QVariant.String, len=12))
        
        if xy:
            # set field precision depending on if CRS is geographic or not
            if crs_xy.isGeographic():
                prec = 6
            else:
                prec = 2
            # create fields for lat_DDM and lon_DDM coordinates in attribute table
            layer.addAttribute(QgsField(x_field, QVariant.Double, len=10, prec=prec))
            layer.addAttribute(QgsField(y_field, QVariant.Double, len=10, prec=prec))
        
        # update attribute table fields
        layer.updateFields()
        
        # get all features
        features = self.get_features(layer, selected=False)
        
        for feature in features:
            # get geometry of feature
            geom = feature.geometry().asPoint()
            
            # transform geometry to EPSG:4326 CRS
            geom4326 = trans4326.transform(geom)
            
            # transform geometry to EPSG:4326 CRS
            geomXY = transXY.transform(geom)
            
            if latlon_DD:
                # set geometry of each feature in the vector layer into seperate fields
                feature.setAttribute(feature.fieldNameIndex(lat_DD_field), geom4326.y())
                feature.setAttribute(feature.fieldNameIndex(lon_DD_field), geom4326.x())
            
            if latlon_DDM:
                # convert DD to DDM
                lat_ddm, lon_ddm = utils.dd2ddm(geom4326.y(), geom4326.x())
                # set DDM geometry of each feature
                feature.setAttribute(feature.fieldNameIndex(lat_DDM_field), lat_ddm)
                feature.setAttribute(feature.fieldNameIndex(lon_DDM_field), lon_ddm)
            
            if xy:
                # set geometry of each feature in the vector layer into seperate fields
                feature.setAttribute(feature.fieldNameIndex(x_field), geomXY.x())
                feature.setAttribute(feature.fieldNameIndex(y_field), geomXY.y())
            
            # update attribute table
            layer.updateFeature(feature)
            
        layer.commitChanges()
        
        return 0, None

    def write_line_length(self, layer, ellipsoid, transform_context, m=False, km=False, nm=False):
        """Write length attribute [m/km/nm] to layer.

        Parameters
        ----------
        layer : QgsVectorLayer
            input line vector layer
        ellipsoid : str
            QgsCoordinateReferenceSystem.ellipsoidAcronym()
        transform_context : QgsCoordinateTransformContext
            transform context for coordinate transformation
        m : boolean
            write meters (Default value = False)
        km : boolean
            write kilometers (Default value = False)
        nm : boolean
            write nautical miles (Default value = False)

        Returns
        -------
        error : boolean
            0/1 - no error/error
        result : str or None
            output or error msg if error == 1

        """
        # if no lengths shall be written, return
        if m == km == nm == False:
            return 1, 'No length units selected, no attributes created!\n'
        
        # set some field names
        prefix = 'length_'
        m_field = f'{prefix}m'
        km_field = f'{prefix}km'
        nm_field = f'{prefix}nm'
        
        # get CRS of input layer
        crs_layer = layer.crs()
        
        # Initialize Distance calculator class with ellipsoid
        da = QgsDistanceArea()
        da.setSourceCrs(crs_layer, transform_context)
        da.setEllipsoid(ellipsoid)
        
        # with edit(layer):
        if not layer.isEditable():
            layer.startEditing()
            
        # delete fields previously created by Cruise Tools
        self.delete_fields_by_prefix(layer, prefix)
        
        # create fields for length_m and/or length_nm
        if m:
            layer.addAttribute(QgsField(m_field, QVariant.Double, len=15, prec=2))
        if km:
            layer.addAttribute(QgsField(km_field, QVariant.Double, len=15, prec=3))
        if nm:
            layer.addAttribute(QgsField(nm_field, QVariant.Double, len=15, prec=3))
        
        # update attribute table fields
        layer.updateFields()
        
        # get all features
        features = self.get_features(layer, selected=False)
        
        for feature in features:
            # get geometry of feature
            geom = feature.geometry()
            
            # measure feature length in meters
            len = da.measureLength(geom)
            
            # set field values according to the calculated length
            if m:
                len_m = da.convertLengthMeasurement(len, QgsUnitTypes.DistanceMeters)
                len_m = round(len_m, 2)
                feature.setAttribute(layer.fields().indexFromName(m_field), len_m)
            if km:
                len_km = da.convertLengthMeasurement(len, QgsUnitTypes.DistanceKilometers)
                len_km = round(len_km, 5)
                feature.setAttribute(layer.fields().indexFromName(km_field), len_km)
            if nm:
                len_nm = da.convertLengthMeasurement(len, QgsUnitTypes.DistanceNauticalMiles)
                len_nm = round(len_nm, 5)
                feature.setAttribute(layer.fields().indexFromName(nm_field), len_nm)
            
            # check if speed_kn exists
            f_idx_speed = layer.fields().indexFromName('speed_kn')
            f_idx_time = layer.fields().indexFromName('time_h')
            if (f_idx_speed != -1) and (f_idx_time != -1):
                # if yes, get value
                speed_kn = feature.attributes()[f_idx_speed]
                if speed_kn is not None:
                    # if value not NULL, calculate time and write it to time_h field
                    len_nm = da.convertLengthMeasurement(len, QgsUnitTypes.DistanceNauticalMiles)
                    time_h = round(len_nm / speed_kn, 2)
                    feature.setAttribute(f_idx_time, time_h)
            
            # update attribute table
            layer.updateFeature(feature)
                
        layer.commitChanges()
        
        return 0, None

    def write_polygon_area(self, layer, ellipsoid, transform_context, m2=False, km2=False):
        """Write area of all polygon features into attribute table.

        Parameters
        ----------
        layer : QgsVectorLayer
            input line vector layer
        ellipsoid : str
            QgsCoordinateReferenceSystem.ellipsoidAcronym()
        transform_context : QgsCoordinateTransformContext
            transform context for coordinate transformation
        m2 : boolean
            write square meters (Default value = False)
        km2 : boolean
            write square kilometers (Default value = False)

        Returns
        -------
        error : boolean
            0/1 - no error/error
        result : str or None
            output or error msg if error == 1

        """
        # if no areas shall be written, return
        if m2 == km2 == False:
            return 1, 'No area units selected, no attributes created!\n'
        
        # set some field names
        prefix = 'area_'
        m2_field = f'{prefix}m2'
        km2_field = f'{prefix}km2'
        
        # get CRS of input layer
        crs_layer = layer.crs()
        
        # Initialize Distance calculator class with ellipsoid
        da = QgsDistanceArea()
        da.setSourceCrs(crs_layer, transform_context)
        da.setEllipsoid(ellipsoid)
        
        # with edit(layer):
        if not layer.isEditable():
            layer.startEditing()
            
        # delete fields previously created by Cruise Tools
        self.delete_fields_by_prefix(layer, prefix)
        
        # create attribute table fields for specified units
        if m2:
            layer.addAttribute(QgsField(m2_field, QVariant.Double, len=15, prec=2))
        if km2:
            layer.addAttribute(QgsField(km2_field, QVariant.Double, len=15, prec=3))
            
        layer.updateFields()
        
        # get all features
        features = self.get_features(layer, selected=False)
        
        for feature in features:
            # get geometry
            geom = feature.geometry()
            
            # area in SQUARE METERS
            area = da.measureArea(geom)
            
            # set field values according to calculated AREA
            if m2:
                area_m2 = da.convertAreaMeasurement(area, QgsUnitTypes.AreaSquareMeters)
                feature.setAttribute(layer.fields().indexFromName(m2_field), area_m2)
            if km2:
                area_km2 = da.convertAreaMeasurement(area, QgsUnitTypes.AreaSquareKilometers)
                feature.setAttribute(layer.fields().indexFromName(km2_field), area_km2)
            
            # update attribute table
            layer.updateFeature(feature)
            
        layer.commitChanges()
        
        return 0, None

    def swap_vectors(self, layer, selected=True):
        """Swap / reverse vector direction for line layers.

        Parameters
        ----------
        layer : QgsVectorLayer
            input line vector layer
        selected : boolean
            swap only selected or all features (Default value = True)

        Returns
        -------
        error : boolean
            0/1 - no error/error
        result : str or None
            output or error msg if error == 1

        """
        # with edit(layer):
        if not layer.isEditable():
            layer.startEditing()
            
        # get features
        features = self.get_features(layer, selected=selected)
        
        # reverse line direction for each (selected) feature
        for feature in features:
            geom = feature.geometry()
            if geom.isMultipart():
                mls = QgsMultiLineString()
                for line in geom.asGeometryCollection():
                    mls.addGeometry(line.constGet().reversed())
                newgeom = QgsGeometry(mls)
                layer.changeGeometry(feature.id(), newgeom)
            else:
                newgeom = QgsGeometry(geom.constGet().reversed())
                layer.changeGeometry(feature.id(), newgeom)
            
        layer.commitChanges()
        
        return 0, None
