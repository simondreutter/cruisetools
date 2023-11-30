import os

from qgis.core import (
    QgsGeometry,
    QgsFeature,
    QgsCoordinateReferenceSystem,
)

from ..vector import Vector
from .. import config

class Planning(Vector):
    """Base class for planning modules."""

    def __init__(self):
        """Initialize Planning."""
        self.module = 'PLANNING'
        self.config = config.CruiseToolsConfig()
        self.plugin_dir = f'{os.path.dirname(__file__)}/..'

    def lines_to_vertices(self, features, fields):
        """Create Vertex features from Line features.

        Parameters
        ----------
        features : QgsFeature list/iterator
            input line features
        fields : QgsFields
            fields to be created for the vertices

        Returns
        -------
        vertices : QgsFeature list
            output vertex features

        """
        # create empty list for vertices
        vertices = []
        
        # fid increment
        i = 1
        
        # loop over input features
        for feature in features:
            # get attributes from input feature
            attributes = feature.attributes()
            
            # get vertex geometry from line geometry
            geom = feature.geometry().asPolyline()
            
            # loop over vertices
            for idx, g in enumerate(geom):
                # create vertex feature
                vertex = QgsFeature(fields)
                
                # set vertex geometry
                vertex.setGeometry(QgsGeometry.fromPointXY(g))
                
                # loop over feature fields
                for field in feature.fields():
                    # if field exists in input fields
                    if field.name() in fields.names():
                        # set attribute from line to vertex
                        if self.add_vertex_suffix and (field.name() == 'name'):  # add order numbering (for default field "name")
                            vertex.setAttribute(field.name(), feature.attribute(field.name()) + f'_{idx + 1:03d}')
                        else:
                            vertex.setAttribute(field.name(), feature.attribute(field.name()))
                
                # set fid
                vertex.setAttribute('fid', i)
                i += 1
                
                # append vertex to vertices list
                vertices.append(vertex)
        
        return vertices

    def get_UTM_zone(self, lat, lon):
        """Get appropriated UTM zone EPSG ID for line feature.

        Parameters
        ----------
        lat : float
            latitude
        lon : float
            longitude

        Returns
        -------
        crs_utm : QgsCoordinateReferenceSystem
            CRS of UTM zone

        """
        # get UTM band from longitude
        utm_band = int((floor((lon + 180) / 6) % 60) + 1)
        
        # get EPSG code from UTM band and latitude (S/N)
        if lat >= 0:
            epsg_code = f'326{utm_band:02d}'
        else:
            epsg_code = f'327{utm_band:02d}'
        
        # create CRS
        crs_utm = QgsCoordinateReferenceSystem(f'EPSG:{epsg_code}')
        
        return crs_utm
