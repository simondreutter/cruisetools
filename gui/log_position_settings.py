from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QGridLayout,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QSpacerItem,
    QSizePolicy,
    QCheckBox,
    QGroupBox,
    QTextEdit,
    QDialogButtonBox,
    QFrame,
    QLineEdit,
    QDialog
)
from PyQt5.QtGui import QFont, QIcon, QValidator

from qgis.gui import (
    QgsMapLayerComboBox,
    QgsCollapsibleGroupBox,
)
from qgis.core import (
    Qgis,
    QgsMapLayerProxyModel,
    QgsWkbTypes,
    QgsMapLayerType,
)

class NotEmptyValidator(QValidator):
    """https://stackoverflow.com/a/63862815."""

    def validate(self, text: str, pos):  # noqa
        if bool(text.strip()):
            state = QValidator.Acceptable
        else:
            state = QValidator.Intermediate  # so that field can be made empty temporarily
        return state, text, pos

class QHLine(QFrame):
    """Horizontal separater line."""

    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class LogPositionSettings(QDialog):
    """Log Position Settings GUI."""

    def __init__(self, first_start: bool):
        """Initialize GUI."""
        super(LogPositionSettings, self).__init__()
        
        self.first_start = first_start
        
        # icon path
        self.icon_path = ':/plugins/cruisetools/icons'
        
        # set window size
        self.resize(600, 500)
        
        # set window icon
        icon = QIcon(f'{self.icon_path}/icon.png')
        self.setWindowIcon(icon)
        
        # set windows title
        self.setWindowTitle('Settings - Log Position')
        
        # init settings
        self.load_settings()
        
        # Initialize dialog layout
        self.init_layout()
        
        # Conncet buttons
        self.connect_buttons()
        
        self.defaults = {
            'write_device' : False,
            'write_depth'  : False,
            'sample_depth' : False,
            'wait_time': 1000,
            'event' : 'Event 1\nEvent 2\n...',
        }

    def init_layout(self):
        """Initialize dialog layout."""
        # create layout
        self.layout = QVBoxLayout()
        
        # ========== Logging Point Layer ==========
        self.label_lyr_pt = QLabel()
        self.label_lyr_pt.setFont(QFont('Default'))
        self.label_lyr_pt.setText('Point layer for position logging')
        self.layout.addWidget(self.label_lyr_pt)
        
        self.comboBox_lyr_pt = QgsMapLayerComboBox()
        self.comboBox_lyr_pt.setFilters(QgsMapLayerProxyModel.PointLayer)
        if self.layer_logging is not None and self.layer_logging.geometryType() == QgsWkbTypes.PointGeometry:
            self.comboBox_lyr_pt.setLayer(self.layer_logging)
        # else:
        #     self.comboBox_raster.setCurrentIndex(1)
        self.layout.addWidget(self.comboBox_lyr_pt)
        
        # ========== PosiView Device ==========
        self.label_device = QLabel()
        self.label_device.setText('PosiView device')
        self.layout.addWidget(self.label_device)
        
        self.comboBox_device = QComboBox()
        self.comboBox_device.addItems(self.devices_names)
        # self.comboBox_device.setCurrentIndex(0)
        if self.device in self.devices_names:
            self.comboBox_device.setCurrentText(str(self.device))
        self.layout.addWidget(self.comboBox_device)
        
        self.checkBox_device = QCheckBox()
        self.checkBox_device.setText('Write PosiView device name to attribute table')
        self.checkBox_device.setChecked(self.write_device)
        self.layout.addWidget(self.checkBox_device)
        
        self.checkBox_depth = QCheckBox()
        self.checkBox_depth.setText('Write vehicle depth to attribute table')
        self.checkBox_depth.setChecked(self.write_depth)
        self.layout.addWidget(self.checkBox_depth)
        
        self.layout.addWidget(QHLine())
        
        # -------------------- MBES RASTER SAMPLING --------------------
        self.groupBox_raster = QGroupBox()
        self.groupBox_raster.setTitle('Sample depth(s) from bathymetry raster layer(s)')
        self.groupBox_raster.setCheckable(True)
        self.groupBox_raster.setChecked(self.sample_depth)
        self.layout.addWidget(self.groupBox_raster)
        
        self.layout_groupBox_raster = QVBoxLayout()
        self.groupBox_raster.setLayout(self.layout_groupBox_raster)
        
        # ========== MBES raster ==========
        self.comboBox_raster = QgsMapLayerComboBox()
        self.comboBox_raster.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.comboBox_raster.layerChanged.connect(self.update_raster_band)
        self.layout_groupBox_raster.addWidget(self.comboBox_raster)  # , 6, 0
        
        self.comboBox_raster_band = QComboBox()  # TODO: update with Raster change
        self.layout_groupBox_raster.addWidget(self.comboBox_raster_band)  # , 7, 0
        
        if self.layer_raster is not None and self.layer_raster.type() == QgsMapLayerType.RasterLayer:
            self.comboBox_raster.setLayer(self.layer_raster)
        else:
            self.layer_raster = self.comboBox_raster.currentLayer()
        
        self.update_raster_band()
        
        # -------------------- ADVANCED SETTINGS --------------------
        self.groupBox_advancedSettings = QgsCollapsibleGroupBox()
        self.groupBox_advancedSettings.setTitle('Advanced settings')
        self.groupBox_advancedSettings.setCheckable(True)
        self.groupBox_advancedSettings.setChecked(False)
        self.groupBox_advancedSettings.setSaveCollapsedState(True)
        
        if self.first_start:
            self.groupBox_advancedSettings.setCollapsed(True)
        
        # init GridLayout for Advanced Settings groupBox
        self.layout_groupBox = QGridLayout(self.groupBox_advancedSettings)
        
        self.label_waitTime = QLabel(self.groupBox_advancedSettings)
        self.label_waitTime.setText('GPS listening time (ms):')
        self.layout_groupBox.addWidget(self.label_waitTime, 0, 0, 1, 1)
        
        self.lineEdit_waitTime = QLineEdit(self.groupBox_advancedSettings)
        self.lineEdit_waitTime.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        # validator = NotEmptyValidator(self.lineEdit_waitTime)
        # self.lineEdit_waitTime.setValidator(validator)
        if self.wait_time != '':
            self.lineEdit_waitTime.setText(str(self.wait_time))
        else:
            self.lineEdit_waitTime.setPlaceholderText('Enter reasonable time (default: 1000 ms)')
        self.layout_groupBox.addWidget(self.lineEdit_waitTime, 0, 1, 1, 1)
        
        #
        self.label_events = QLabel(self.groupBox_advancedSettings)
        self.label_events.setText('Insert list of pre-defined events for logging drop-down menu (one per line):')
        self.layout_groupBox.addWidget(self.label_events, 1, 0, 1, -1)
        
        self.textEdit_events = QTextEdit(self.groupBox_advancedSettings)
        if self.events == ['']:
            self.textEdit_events.setPlaceholderText('Event 1\nEvent 2\n...')
        else:
            self.textEdit_events.setText('\n'.join(self.events))
        self.layout_groupBox.addWidget(self.textEdit_events, 2, 0, 2, -1)
        
        # add Advanced Settings groupBox
        self.layout.addWidget(self.groupBox_advancedSettings)
        # ------------------------------------------------------------

        # add vertical spacer
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.layout.addItem(self.verticalSpacer)
        
        # add line separator
        self.layout.addWidget(QHLine())
        
        # init buttons
        self.buttonBox = QDialogButtonBox()
        self.buttonBox.setStandardButtons(
            QDialogButtonBox.Cancel | QDialogButtonBox.Apply | QDialogButtonBox.RestoreDefaults
        )
        self.buttonBox.button(QDialogButtonBox.Apply).setToolTip('Apply & save settings')
        self.layout.addWidget(self.buttonBox)
        
        # set window layout
        self.setLayout(self.layout)

    def connect_buttons(self):
        """Connect dialog buttons."""
        self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.apply_and_accept)
        # self.buttonBox.rejected.connect(self.reject)
        self.buttonBox.button(QDialogButtonBox.Cancel).clicked.connect(self.cancel)
        self.buttonBox.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self.restoreDefaultSettings)

    def apply_and_accept(self):
        """Apply settings and accept Dialog."""
        self.apply_settings()
        self.accept()

    def cancel(self):
        """Cancel settings dialog and perform sanity checks."""
        # sanity check
        self.wait_time = self.defaults.get('wait_time') if self.wait_time == '' else int(self.wait_time)
        
        # reject changes
        self.reject()

    def update_raster_band(self, vector_layer=None):
        """Update raster band comboBox."""
        self.comboBox_raster_band.clear()
        
        # get currently selected raster layer
        self.layer_raster = self.comboBox_raster.currentLayer()
        
        if self.layer_raster is not None:
            self.bandCount = self.layer_raster.bandCount()
            if self.bandCount == 1:
                self.band_names = ['Band 1 (Grey)']
            else:
                self.band_names = [self.layer_raster.bandName(i) for i in range(self.bandCount)]
            
            # add band options for currently selected raster
            self.comboBox_raster_band.addItems(self.band_names)

    def apply_settings(self):
        """Apply and save save settings."""
        self.layer_logging = self.comboBox_lyr_pt.currentLayer()
        
        self.device = self.comboBox_device.currentText()
        
        self.write_device = self.checkBox_device.isChecked()
        
        self.write_depth = self.checkBox_device.isChecked()
        
        self.sample_depth = self.groupBox_raster.isChecked()
        
        self.layer_raster = self.comboBox_raster.currentLayer()
        
        self.raster_band_name = self.comboBox_raster_band.currentText()
        if self.raster_band_name != '':
            self.raster_band = self.band_names.index(self.raster_band_name) + 1
        
        wait_time = self.lineEdit_waitTime.text()
        self.wait_time = int(wait_time) if wait_time != '' else self.defaults.get('wait_time')
                
        event = self.textEdit_events.toPlainText()
        self.events = [e for e in event.split('\n') if e != '']
        
        # update config
        if self.layer_logging is not None:
            self.config.set(self.module, 'layer_logging', self.layer_logging.name())
        
        if self.device != '':
            self.config.set(self.module, 'device', self.device)
            self.config.set(self.module, 'write_device', self.write_device)
            self.config.set(self.module, 'write_depth', self.write_depth)
        
        self.config.set(self.module, 'sample_depth', self.sample_depth)
        if self.sample_depth:
            self.config.set(self.module, 'layer_raster', self.layer_raster.name())
            self.config.set(self.module, 'raster_band', self.raster_band)
        
        self.config.set(self.module, 'wait_time', self.wait_time)
        self.config.set(self.module, 'events', ';'.join(self.events))
        
        self.iface.messageBar().pushMessage(
            'Log Position ', 'Saved user settings to Cruise Tools config', level=Qgis.Success, duration=2
        )

    def restoreDefaultSettings(self):
        """Restore default settings."""
        self.sample_depth = False
        self.groupBox_raster.setChecked(self.defaults.get('sample_depth', False))
        
        self.checkBox_device.setChecked(self.defaults.get('write_device', False))
        
        self.lineEdit_waitTime.setText(str(self.defaults.get('wait_time', 1000)))
        self.groupBox_advancedSettings.setChecked(False)
        
        self.events = []
        self.textEdit_events.clear()
        self.textEdit_events.setPlaceholderText(self.defaults.get('event', ''))

    def load_settings(self):
        """Load Cruise Tools settings."""
        self.layer_logging = self.config.get(self.module, 'layer_logging', fallback='')
        if self.layer_logging != '':  # get layer from name
            self.layer_logging = self.project.mapLayersByName(self.layer_logging)
            if self.layer_logging != []:
                self.layer_logging = self.layer_logging[0]
            else:
                self.layer_logging = None
        else:
            self.layer_logging = None
        
        self.device = self.config.get(self.module, 'device', fallback='')
        self.write_device = self.config.getboolean(self.module, 'write_device', fallback=False)
        self.write_depth = self.config.getboolean(self.module, 'write_depth', fallback=False)
        
        self.sample_depth = self.config.getboolean(self.module, 'sample_depth', fallback=False)
        
        self.layer_raster = self.config.get(self.module, 'layer_raster', fallback='')
        if self.layer_raster != '':  # get layer from name
            self.layer_raster = self.project.mapLayersByName(self.layer_raster)
            if self.layer_raster != []:
                self.layer_raster = self.layer_raster[0]
            else:
                self.layer_raster = None
        else:
            self.layer_raster = None
        
        self.raster_band = self.config.getint(self.module, 'raster_band', fallback=1)
        
        # ---------- ADVANCED SETTINGS ----------
        self.wait_time = self.config.getint(self.module, 'wait_time', fallback=1000)
        self.events = self.config.get(self.module, 'events', fallback='').split(';')
