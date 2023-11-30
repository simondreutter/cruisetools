import datetime

from qgis.core import (
    Qgis,
    QgsField,
    QgsGeometry,
    QgsPointXY,
    QgsEditorWidgetSetup,
    QgsVectorLayerUtils,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
)

from qgis.PyQt.QtCore import pyqtSlot
from PyQt5 import QtTest
from PyQt5.QtCore import Qt, QDateTime, QVariant

from .logging import Logging
from ..gui.log_position_settings import LogPositionSettings

class LogPosition(LogPositionSettings, Logging):
    """Base class for logging survey position."""

    def __init__(self, first_start: bool = False):
        """Initialize Log Position."""
        super(LogPosition, self).__init__(first_start)
        
        # set default CRS for GPS coordinates
        self.crs_gps = QgsCoordinateReferenceSystem.fromEpsgId(4326)
        
        # init data stream variables
        self.stream = dict()
        
        # init validation variable
        self.valid_position = False
        
        # set config for datetime field
        self.config_field_datetime = {
            'allow_null': True,
            'calendar_popup': True,
            'display_format': 'yyyy-MM-ddTHH:mm:ssZ',
            'field_format': 'Qt ISO Date',
            'field_iso_format': True
        }

    @pyqtSlot(dict)
    def process_datastream(self, data):
        """Process incoming GPS data stream."""
        # define validation checks
        check_filter = (
            data['id'] == self.provider_filter['id']
            if self.provider_filter['id'] not in (None, 'None')
            else True
        )
        check_coords = all(c in data.keys() for c in ('lat', 'lon'))
        
        # update GPS stream dict
        if check_filter and check_coords:
            self.stream.update(data)
        #elif not check_filter:
        #    print('filtered')
        #elif not check_coords:
        #    print('no coords')
        
        # check for valid coordinates in stream dict after listening for `self.wait_time` ms
        if all(c in self.stream.keys() for c in ('lat', 'lon')):
            self.valid_position = True
        else:
            self.valid_position = False

    def get_current_position(self, wait: int = 1000):
        """Get current position from incoming GPS data stream."""
        # connect to GPS data stream
        self.device_provider.newDataReceived.connect(self.process_datastream)
        
        # listen for `wait` ms
        QtTest.QTest.qWait(wait)
        
        # disconnect from GPS data stream
        self.device_provider.newDataReceived.disconnect(self.process_datastream)

    def access_posiview_data_provider(self):
        """Access PosiView data provider for selected device."""
        # get PosiView provider name and (optional) filter(s) for device
        self.provider_name, self.provider_filter = [(k, v) for k, v in self.device_properties.get(self.device).items()][0]
        self.device_provider = self.posiview_project.dataProviders[self.provider_name]
        # print('self.provider_name:', self.provider_name)
        # print('self.provider_filter:', self.provider_filter)
        
        # reset variables
        self.stream = {}
        self.valid_position = False
        # print('self.stream:', self.stream)  # FIXME
        
        # check for valid GPS information
        n_retries = 0
        while self.stream == {}:
            self.get_current_position(wait=self.wait_time)
            n_retries += 1
            # print(f'self.stream ({n_retries}: {self.valid_position}):', self.stream)  # FIXME
            if n_retries == 5:
                self.iface.messageBar().pushMessage(
                    'Log Position ',
                    (
                        'No vaild coordinate information available! '
                        'Please check the PosiView data provider for your device '
                        'or increase the GPS listening time!'
                    ),
                    level=Qgis.Critical,
                    duration=0
                )
                break
        
        if self.valid_position:
            self.info = self.stream
        else:
            self.info = {}

    def add_logged_position(self):
        """Add logged position as new feature to selected Point layer."""
        self.layer_logging_provider = self.layer_logging.dataProvider()
        self.fields = self.layer_logging.fields()
        self.field_names = self.fields.names()
        
        # get CRS of Point layer
        self.crs_layer_logging = self.layer_logging.crs()
        self.crs_layer_logging_id = self.crs_layer_logging.postgisSrid()
        
        # get CRS of Raster layer
        if self.sample_depth:
            self.crs_layer_raster = self.layer_raster.crs()
        
        # init Point
        self.pt = QgsPointXY(self.info.get('lon'), self.info.get('lat'))
        
        # transform Point to raster CRS if not identical
        if self.sample_depth:
            if self.crs_layer_logging != self.crs_layer_raster:
                transformer_latlon2raster = QgsCoordinateTransform(
                    self.crs_gps, self.crs_layer_raster, project=self.project
                )
                self.pt_raster = transformer_latlon2raster.transform(self.pt)
            else:
                self.pt_raster = self.pt
        
        # transform Point to logging layer CRS if not EPSG:4326
        if self.crs_layer_logging != self.crs_gps:
            self.add_xy = True
            transformer_latlon2vector = QgsCoordinateTransform(
                self.crs_gps, self.crs_layer_logging, project=self.project
            )
            self.pt_xy = transformer_latlon2vector.transform(self.pt)
        else:
            self.add_xy = False
            self.pt_xy = self.pt
        
        # get vehicle depth if required
        if self.write_depth:
            if 'depth' in self.info.keys():
                self.depth_vehicle = self.info.get('depth')
            else:
                self.depth_vehicle = 0
        
        # sample depth if required
        if self.sample_depth:
            self.depth_seafloor, self.depth_valid = self.layer_raster.dataProvider().sample(self.pt_raster, self.raster_band)
        
        # ===== START EDITING =====
        if not self.layer_logging.isEditable():
            # print('[CAPTURE]    Start editing Point layer')  # FIXME
            self.layer_logging.startEditing()
        
        # ----- ADD FIELDS (if not already set) -----
        fields_to_add = []
        
        # add UTC timestamp
        field_datetime = 'datetime_UTC'
        if field_datetime not in self.field_names:
            fields_to_add.append(QgsField(field_datetime, type=QVariant.DateTime))
        
        # add LAT / LON fields if not in layer fields
        fields_coords = ['lat_DD', 'lon_DD']
        kwargs_deg = dict(type=QVariant.Double, len=10, prec=6)
        if not all(f in fields_coords for f in self.fields):
            for fname in fields_coords:
                if fname not in self.field_names:
                    fields_to_add.append(QgsField(fname, **kwargs_deg))
        
        # add XY fields if not in layer fields AND layer not geographic
        fields_coords_xy = [f'x_{self.crs_layer_logging_id}', f'y_{self.crs_layer_logging_id}']
        if self.add_xy and self.crs_layer_logging != self.crs_gps:
            kwargs_xy = dict(type=QVariant.Double, len=12, prec=2)
            if not all(f in fields_coords_xy for f in self.fields):
                for fname in fields_coords_xy:
                    if fname not in self.field_names:
                        fields_to_add.append(QgsField(fname, **kwargs_xy))
        
        # add vehicle depth field
        field_vehicle_depth = 'vehicle_depth_m'
        if self.write_depth:
            if field_vehicle_depth not in self.field_names:
                fields_to_add.append(QgsField(field_vehicle_depth, type=QVariant.Double, len=8, prec=2))
        
        # add seafloor depth field
        field_depth_seafloor = 'depth_seafloor_m'
        if self.sample_depth:
            if field_depth_seafloor not in self.field_names:
                fields_to_add.append(QgsField(field_depth_seafloor, type=QVariant.Double, len=8, prec=2))
        
        # add PosiView device field
        field_device = 'PosiView_device'
        if self.write_device:
            if field_device not in self.field_names:
                fields_to_add.append(QgsField(field_device, type=QVariant.String, len=25))
        
        # add event field
        field_event = 'event'
        if self.events != []:
            if field_event not in self.field_names:
                fields_to_add.append(QgsField(field_event, type=QVariant.String, len=25))
        
        # add note field
        field_note = 'note'
        if field_note not in self.field_names:
            fields_to_add.append(QgsField(field_note, type=QVariant.String, len=0))
        
        # update layer fields
        self.layer_logging_provider.addAttributes(fields_to_add)
        self.layer_logging.updateFields()
        fields = self.layer_logging.fields()  # get updated reference to self.layer_logging fields
        
        # ----- SET FEATURE ATTRIBUTES -----
        # get UTC timestamp field ID
        id_dt_utc = fields.lookupField(field_datetime)
        if fields[id_dt_utc].editorWidgetSetup().config() != self.config_field_datetime:
            self.layer_logging.setEditorWidgetSetup(id_dt_utc, QgsEditorWidgetSetup('DateTime', self.config_field_datetime))
        
        # get LAT / LON coordinates IDs
        id_lat_DD, id_lon_DD = [fields.lookupField(f) for f in fields_coords]
                
        if self.add_xy:
            id_x, id_y = [fields.lookupField(f) for f in fields_coords_xy]
        
        # get vehicle depth field ID
        if self.write_depth:
            id_depth = fields.lookupField(field_vehicle_depth)
        
        # get seafloor depth field ID
        if self.sample_depth:
            id_seafloor = fields.lookupField(field_depth_seafloor)
        
        # get PosiView device field
        if self.write_device:
            id_device = fields.lookupField(field_device)
        
        # needed to reset QgsEditorWidgetSetup if no event list defined
        id_event = fields.lookupField(field_event)
        
        timestamp_utc = QDateTime(
            datetime.datetime.utcfromtimestamp(self.info['time'])
            if 'time' in self.info.keys()
            else datetime.datetime.utcnow()
        )
        timestamp_utc.setTimeSpec(Qt.UTC)  # declare QDateTime as UTC time (for QGIS)
        feat_attributes = {
            id_dt_utc : timestamp_utc,
            id_lat_DD : round(self.pt.y(), 6),
            id_lon_DD : round(self.pt.x(), 6),
        }
        if self.add_xy:
            feat_attributes[id_x] = round(self.pt_xy.x(), 2)
            feat_attributes[id_y] = round(self.pt_xy.y(), 2)
        if self.write_depth:
            feat_attributes[id_depth] = round(self.depth_vehicle, 2)
        if self.sample_depth and self.depth_valid:
            feat_attributes[id_seafloor] = round(self.depth_seafloor, 2)
        if self.write_device:
            feat_attributes[id_device] = self.device
        if self.events != []:
            editor_widget_event = QgsEditorWidgetSetup(
                'ValueMap', {'map': dict(zip(self.events, self.events))}
            )
        else:
            editor_widget_event = QgsEditorWidgetSetup('TextEdit', {'IsMultiline': False, 'UseHtml': False})
        if id_event != -1:
            self.layer_logging.setEditorWidgetSetup(id_event, editor_widget_event)
            
        # ----- CREATE FEATURE -----
        feat = QgsVectorLayerUtils.createFeature(
            self.layer_logging,
            QgsGeometry.fromPointXY(self.pt_xy),
            feat_attributes,
            self.layer_logging.createExpressionContext()
        )
        # add new Point feature to layer
        self.layer_logging_provider.addFeature(feat)
        
        # open interactive attribute dialog
        self.iface.openFeatureForm(self.layer_logging, feat)
        
        # ===== END EDITING =====
        self.layer_logging.commitChanges()

    def log_position(self):
        """Log current position."""
        # retrieve available data provider from PosiView plugin
        self.access_posiview_data_provider()
        
        if self.valid_position:
            # insert logged position as Point to selected map layer
            self.add_logged_position()

    def update_devices(self):
        """Update PosiView devices (mobiles)."""
        # get current PosiView devices
        self.get_devices()
        
        # update QComboBox in settings dialog
        self.comboBox_device.clear()
        self.comboBox_device.addItems(self.devices_names)
        self.comboBox_device.setCurrentText(str(self.device))
