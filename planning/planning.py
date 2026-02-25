import csv
import os

from qgis.core import QgsGeometry
from qgis.core import QgsFeature
from qgis.core import NULL

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

            # get geometry from input feature
            geom_f = feature.geometry()

            # empty list for geometry parts
            geoms = []

            # check if geometry is multipart
            # and convert from line to vertex geometry
            if geom_f.isMultipart():
                for part in geom_f.asMultiPolyline():
                    geoms.append(part)
            else:
                geoms = [geom_f.asPolyline()]

            # iterate through geometry parts
            for geom in geoms:
                # loop over vertices
                for idx, pnt in enumerate(geom):
                    # create vertex feature
                    vertex = QgsFeature(fields)

                    # set vertex geometry
                    vertex.setGeometry(QgsGeometry.fromPointXY(pnt))

                    # loop over feature fields
                    for field in feature.fields():
                        # if field exists in input fields
                        if field.name() in fields.names():
                            # set attribute from line to vertex
                            if self.vertex_suffix and (
                                    field.name() == 'name'):  # add order numbering (for default field "name")
                                vertex.setAttribute(field.name(), feature.attribute(field.name()) + f'_{idx + 1:03d}')
                            else:
                                vertex.setAttribute(field.name(), feature.attribute(field.name()))

                    # set fid
                    vertex.setAttribute('fid', i)
                    i += 1

                    # append vertex to vertices list
                    vertices.append(vertex)

        return vertices

    def export_csv(self, table, output):
        """Export points to CSV file.

        Parameters
        ----------
        table : list
            list of feature dictionaries created with
                dict = dict(zip(fields, attributes))
                dict['lat_DD'] = lat
                dict['lon_DD'] = lon
        output : str
            output CSV file

        Returns
        -------
        error : boolean
            0/1 - no error/error
        result : str
            output path or error msg if error == 1

        """
        # map for different geometry types
        geometry_map = {
            'Loxodrome': 'Rhumbline',
            'loxodrome': 'Rhumbline',
            'L': 'Rhumbline',
            'l': 'Rhumbline',
            'Rhumb Line': 'Rhumbline',
            'rhumb line': 'Rhumbline',
            'Rhumbline': 'Rhumbline',
            'rhumbline': 'Rhumbline',
            'RL': 'Rhumbline',
            'rl': 'Rhumbline',
            'Orthodrome': 'Great Circle',
            'orthodrome': 'Great Circle',
            'O': 'Great Circle',
            'o': 'Great Circle',
            'Great Circle': 'Great Circle',
            'great circle': 'Great Circle',
            'Greatcircle': 'Great Circle',
            'greatcircle': 'Great Circle',
            'GC': 'Great Circle',
            'gc': 'Great Circle'
        }

        # open CSV file
        with open(output, 'w', newline='', encoding='ansi') as csvfile:
            # write CSV header
            writer = csv.writer(csvfile, dialect='excel', delimiter=';',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
            header = [x for x in table[0].keys()]
            writer.writerow(header)

            # iterate over points in table
            for feature in table:
                # normalize geometry type
                geometry_type = feature.get('geometry_type')
                if geometry_type:
                    feature['geometry_type'] = geometry_map.get(str(geometry_type).strip())

                # write row
                row = [str(feature[key]).replace('NULL', '').replace('None', '') for key in feature.keys()]
                writer.writerow(row)

        return 0, output

    def export_rtz(self, table, output,
                   line=False,
                   duplicate_precision=6,
                   radius_fallback=0.5):
        """Export points to RTZ ECDIS Route Exchange 1.1 format.

        Parameters
        ----------
        table : list
            list of feature dictionaries created with
                dict = dict(zip(fields, attributes))
                dict['lat_DD'] = lat
                dict['lon_DD'] = lon
        output : str
            output RTZ file
        line : bool
            line switch. If True, name will be ignored and waypoint
            names will be 'WP1', 'WP2', 'WP3', ...
        duplicate_precision : int
            decimal precision to check coordinate duplicates (Default value = 6)
        radius_fallback : float
            turn radius fallback in base not supplied
            turn radius is expected to be in a
                turn_radius_nm
            field. (Default value = 0.5)

        Returns
        -------
        error : boolean
            0/1 - no error/error
        result : str
            output path or error msg if error == 1

        """
        # route name
        route_name = os.path.splitext(os.path.basename(output))[0]

        # map for different geometry types
        geometry_map = {
            'Loxodrome': 'Loxodrome',
            'loxodrome': 'Loxodrome',
            'L': 'Loxodrome',
            'l': 'Loxodrome',
            'Rhumb Line': 'Loxodrome',
            'rhumb line': 'Loxodrome',
            'Rhumbline': 'Loxodrome',
            'rhumbline': 'Loxodrome',
            'RL': 'Loxodrome',
            'rl': 'Loxodrome',
            'Orthodrome': 'Orthodrome',
            'orthodrome': 'Orthodrome',
            'O': 'Orthodrome',
            'o': 'Orthodrome',
            'Great Circle': 'Orthodrome',
            'great circle': 'Orthodrome',
            'Greatcircle': 'Orthodrome',
            'greatcircle': 'Orthodrome',
            'GC': 'Orthodrome',
            'gc': 'Orthodrome'
        }

        # header infos
        ns = 'http://www.cirm.org/RTZ/1/1'
        xsi = 'http://www.w3.org/2001/XMLSchema-instance'
        rtz_version = '1.1'

        # some on-land position as a reference for position duplicates
        last_lat = round(53.538838624722324, duplicate_precision)
        last_lon = round(8.579902559296466, duplicate_precision)

        # empty XML string for waypoint tags
        waypoints_xml = ''

        # iterate over points in table
        for feature in table:
            # get the id / fid
            wp_id = feature.get('fid')

            # get coordinates
            lat = feature['lat_DD']
            lon = feature['lon_DD']

            # round (down) coordinates to check against close duplicates
            lat_dup = round(lat, duplicate_precision)
            lon_dup = round(lon, duplicate_precision)

            # check coordinates
            if (lat_dup, lon_dup) == (last_lat, last_lon):
                continue

            # use current coordinates as reference for next feature
            last_lat = lat_dup
            last_lon = lon_dup

            # optional attributes
            # waypoint name
            if line:
                name_attr = f' name="WP{wp_id}"'
            else:
                name = feature.get('name')
                if name:
                    name_attr = f' name="{name}"'
                else:
                    name_attr = ''

            # turn radius
            radius_val = feature.get('turn_radius_nm')
            if not radius_val:
                radius_val = radius_fallback
            radius_attr = f' radius="{float(radius_val):.2f}"'

            # build waypoint open tag
            waypoint_block = (
                f'        <waypoint id="{wp_id}"{name_attr}{radius_attr}>\n'
                f'            <position lat="{lat:.8f}" lon="{lon:.8f}"/>\n'
            )

            # ----- leg handling -----
            # cross track distance
            xtd_port = feature.get('xtd_port_nm')
            xtd_stb = feature.get('xtd_stb_nm')
            # navigation geometry (Loxodrome or Orthodrome)
            geometry_type = feature.get('geometry_type')
            # speed
            speed_max = feature.get('speed_kn')
            # notes
            notes = feature.get('notes')

            # normalize geometry type
            if geometry_type:
                geometry_type = geometry_map.get(str(geometry_type).strip(), None)

            # check if leg section at all necessary
            has_leg = (xtd_port not in [NULL, None] or
                       xtd_stb not in [NULL, None] or
                       geometry_type not in [NULL, None] or
                       speed_max not in [NULL, None] or
                       notes not in [NULL, None])
            if has_leg:
                leg_attributes = ''

                # symmetric XTD handling
                if xtd_port not in [NULL, None, ''] and xtd_stb in [NULL, None, '']:
                    xtd_stb = xtd_port
                if xtd_stb not in [NULL, None, ''] and xtd_port in [NULL, None, '']:
                    xtd_port = xtd_stb

                if xtd_port not in [NULL, None, '']:
                    # fit XTD to 0 <= XTD < 10
                    xtd_port = max(0.0, min(9.99, float(xtd_port)))
                    xtd_stb = max(0.0, min(9.99, float(xtd_stb)))
                    leg_attributes += f' portsideXTD="{float(xtd_port):.2f}"'
                    leg_attributes += f' starboardXTD="{float(xtd_stb):.2f}"'

                if geometry_type not in [NULL, None, '']:
                    leg_attributes += f' geometryType="{geometry_type}"'

                if speed_max not in [NULL, None, '']:
                    if speed_max > 0:
                        leg_attributes += f' speedMax="{float(speed_max):.2f}"'

                if notes not in [NULL, None, '']:
                    leg_attributes += f' legReport="{notes}"'

                # add leg to waypoint block
                waypoint_block += f'            <leg{leg_attributes}/>\n'

            # close waypoint block
            waypoint_block += '        </waypoint>\n'

            # add waypoint to other waypoints
            waypoints_xml += waypoint_block

        # finalize XML
        xml_content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<route xmlns="{ns}" xmlns:xsi="{xsi}" version="{rtz_version}">\n'
            f'    <routeInfo routeName="{route_name}" routeStatus="Created with Cruise Tools">\n'
            f'    </routeInfo>\n'
            f'    <waypoints>\n'
            f'{waypoints_xml}'
            f'    </waypoints>\n'
            f'</route>\n'
        )

        # write XML file
        with open(output, 'w', newline='\r\n', encoding='utf-8') as f:
            f.write(xml_content)

        return 0, output

    def export_sam(self, table, output,
                   line,
                   duplicate_precision=6,
                   radius_fallback=0.5):
        """Export points to SAM Route Exchange format compatible CSV file.

        Parameters
        ----------
        table : list
            list of feature dictionaries created with
                dict = dict(zip(fields, attributes))
                dict['lat_DD'] = lat
                dict['lon_DD'] = lon
        output : str
            output CSV file
        line : bool
            line switch. If True, name will be ignored and waypoint
            names will be 'WP1', 'WP2', 'WP3', ...
        duplicate_precision : int
            decimal precision to check coordinate duplicates (Default value = 6)
        radius_fallback : float
            turn radius fallback in base not supplied
            turn radius is expected to be in a
                turn_radius_nm
            field. (Default value = 0.5)

        Returns
        -------
        error : boolean
            0/1 - no error/error
        result : str
            output path or error msg if error == 1

        """
        # map for different geometry types
        geometry_map = {
            'Loxodrome': 'Rhumbline',
            'loxodrome': 'Rhumbline',
            'L': 'Rhumbline',
            'l': 'Rhumbline',
            'Rhumb Line': 'Rhumbline',
            'rhumb line': 'Rhumbline',
            'Rhumbline': 'Rhumbline',
            'rhumbline': 'Rhumbline',
            'RL': 'Rhumbline',
            'rl': 'Rhumbline',
            'Orthodrome': 'Great Circle',
            'orthodrome': 'Great Circle',
            'O': 'Great Circle',
            'o': 'Great Circle',
            'Great Circle': 'Great Circle',
            'great circle': 'Great Circle',
            'Greatcircle': 'Great Circle',
            'greatcircle': 'Great Circle',
            'GC': 'Great Circle',
            'gc': 'Great Circle'
        }

        # some on-land position as a reference for position duplicates
        last_lat = round(53.538838624722324, duplicate_precision)
        last_lon = round(8.579902559296466, duplicate_precision)

        # open CSV file
        with open(output, 'w', newline='', encoding='ansi') as csvfile:
            # write CSV header
            writer = csv.writer(csvfile, dialect='excel', delimiter=';',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
            header = ['Name',
                      'Latitude [°]',
                      'Longitude [°]',
                      'Turn Radius [NM]',
                      'Max.Speed[kn]',
                      'XTD[m]',
                      'Sailmode',
                      'Additional Notes']
            writer.writerow(header)

            # iterate over points in table
            for feature in table:
                # get the id / fid
                wp_id = feature.get('fid')

                # get coordinates
                lat = feature['lat_DD']
                lon = feature['lon_DD']

                # round (down) coordinates to check against close duplicates
                lat_dup = round(lat, duplicate_precision)
                lon_dup = round(lon, duplicate_precision)

                # check coordinates
                if (lat_dup, lon_dup) == (last_lat, last_lon):
                    continue

                # use current coordinates as reference for next feature
                last_lat = lat_dup
                last_lon = lon_dup

                # optional attributes
                # waypoint name
                if line:
                    name = f'WP{wp_id}'
                else:
                    name = feature.get('name')

                # turn radius
                radius_val = feature.get('turn_radius_nm')
                if not radius_val:
                    radius_val = radius_fallback

                # cross track distance
                xtd_port = feature.get('xtd_port_nm')
                if xtd_port == NULL:
                    xtd_port = None
                xtd_stb = feature.get('xtd_stb_nm')
                if xtd_stb == NULL:
                    xtd_stb = None

                # symmetric XTD handling
                if xtd_port not in [NULL, None, ''] and xtd_stb in [NULL, None, '']:
                    xtd_stb = xtd_port
                if xtd_stb not in [NULL, None, ''] and xtd_port in [NULL, None, '']:
                    xtd_port = xtd_stb

                if xtd_port not in [NULL, None, '']:
                    if xtd_port > xtd_stb:
                        xtd_stb = xtd_port
                    elif xtd_stb > xtd_port:
                        xtd_port = xtd_stb
                    # fit XTD to 0 <= XTD < 10
                    xtd_port = max(0.0, min(9.99, float(xtd_port)))
                    xtd_stb = max(0.0, min(9.99, float(xtd_stb)))

                # navigation geometry (Loxodrome or Orthodrome)
                geometry_type = feature.get('geometry_type')
                if geometry_type == NULL:
                    geometry_type = None

                # speed
                speed_max = feature.get('speed_kn')
                if speed_max == NULL:
                    speed_max = None

                # notes
                notes = feature.get('notes')
                if notes == NULL:
                    notes = None

                # normalize geometry type
                if geometry_type:
                    geometry_type = geometry_map.get(str(geometry_type).strip())

                # write point to file
                if speed_max:
                    speed_max = round(speed_max, 2)
                if xtd_port:
                    xtd_port = round(xtd_port, 2)
                row = [name,
                       round(lat, 6),
                       round(lon, 6),
                       round(radius_val, 2),
                       speed_max,
                       xtd_port,
                       geometry_type,
                       notes]

                writer.writerow(row)

        return 0, output
