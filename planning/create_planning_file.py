from pathlib import Path

from qgis.core import QgsField
from qgis.core import QgsFields
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsProcessingParameterCrs
from qgis.core import QgsProcessingParameterEnum
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsCoordinateReferenceSystem
from qgis.core import QgsProcessingException
from qgis.core import QgsProcessingUtils
from qgis.core import QgsWkbTypes

from qgis.PyQt.QtCore import QCoreApplication, QMetaType
from qgis.PyQt.QtGui import QIcon

from .planning import Planning
from .. import utils


class CreatePlanningFile(QgsProcessingAlgorithm, Planning):
    """Create Planning File."""

    # Processing parameters
    # inputs:
    FILE_TYPE = 'FILE_TYPE'
    CRS = 'CRS'
    SPEED = 'SPEED'
    MBES = 'MBES'
    NAV = 'NAV'
    # outputs:
    OUTPUT = 'OUTPUT'

    def __init__(self):
        """Initialize CreatePlanningFile."""
        super(CreatePlanningFile, self).__init__()

        # style files for planning layer
        self.style_planning_lines = self.plugin_dir / 'styles' / 'style_planning_lines.qml'
        self.style_planning_points = self.plugin_dir / 'styles' / 'style_planning_points.qml'

        # initialize default configuration
        self.initConfig()

    def initConfig(self):
        """Get default values from CruiseToolsConfig."""
        self.file_type = self.config.getint(self.module, 'file_type')
        self.default_crs = self.config.get(self.module, 'default_crs')
        self.crs = QgsCoordinateReferenceSystem()
        self.crs.createFromString(self.default_crs)
        self.speed = self.config.getboolean(self.module, 'speed')
        self.mbes = self.config.getboolean(self.module, 'mbes')
        self.nav = self.config.getboolean(self.module, 'nav')

    def initAlgorithm(self, config=None):
        self.file_types = [self.tr('Point planning'),
                           self.tr('Line planning')]
        self.addParameter(
            QgsProcessingParameterEnum(
                name=self.FILE_TYPE,
                description=self.tr('Planning file type'),
                options=self.file_types,
                defaultValue=self.file_type,
                optional=False,
                allowMultiple=False)
        )
        self.addParameter(
            QgsProcessingParameterCrs(
                name=self.CRS,
                description=self.tr('Output CRS'),
                optional=True,
                defaultValue=self.crs)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.SPEED,
                description=self.tr('Add speed and time fields'),
                optional=False,
                defaultValue=self.speed)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.MBES,
                description=self.tr('Add multibeam swath angle fields'),
                optional=False,
                defaultValue=self.mbes)
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                name=self.NAV,
                description=self.tr('Add navigation fields'),
                optional=False,
                defaultValue=self.nav)
        )
        self.addParameter(
            QgsProcessingParameterFeatureSink(
                name=self.OUTPUT,
                description=self.tr('Planning file'),
                type=QgsProcessing.SourceType.TypeVectorLine,
                defaultValue=None,
                optional=False,
                createByDefault=True)
        )

    def processAlgorithm(self, parameters, context, feedback):
        # get input variables as self.* for use in post-processing
        file_type = self.parameterAsEnum(parameters, self.FILE_TYPE, context)
        crs = self.parameterAsCrs(parameters, self.CRS, context)
        speed = self.parameterAsBoolean(parameters, self.SPEED, context)
        mbes = self.parameterAsBoolean(parameters, self.MBES, context)
        nav = self.parameterAsBoolean(parameters, self.NAV, context)

        # if CRS is None, use project CRS
        if not crs.isValid():
            crs = context.project().crs()

        # set new default values in config
        feedback.pushConsoleInfo(self.tr('Storing new default settings in config...'))
        self.config.set(self.module, 'file_type', file_type)
        self.config.set(self.module, 'default_crs', crs.authid())
        self.config.set(self.module, 'speed', speed)
        self.config.set(self.module, 'mbes', mbes)
        self.config.set(self.module, 'nav', nav)

        # check for type (point or line) and set create parameters
        if file_type == 0:
            geom_type = QgsWkbTypes.Type.Point
        elif file_type == 1:
            geom_type = QgsWkbTypes.Type.LineString

        # fields to be created
        fields = QgsFields()

        # add fields
        feedback.pushConsoleInfo(self.tr('Creating output fields...'))
        fields.append(QgsField('name', QMetaType.Type.QString, '', 0, 0))
        if speed:
            fields.append(QgsField('speed_kn', QMetaType.Type.Double, '', 4, 2))
            fields.append(QgsField('time_h', QMetaType.Type.Double, '', 4, 2))
        if mbes:
            fields.append(QgsField('mbes_swath_angle', QMetaType.Type.Int, '', 3, 0))
            fields.append(QgsField('mbes_swath_angle_port', QMetaType.Type.Int, '', 3, 0))
            fields.append(QgsField('mbes_swath_angle_stb', QMetaType.Type.Int, '', 3, 0))
        if nav:
            fields.append(QgsField('turn_radius_nm', QMetaType.Type.Double, '', 4, 2))
            fields.append(QgsField('geometry_type', QMetaType.Type.QString, '', 0, 0))
            fields.append(QgsField('xtd_port_nm', QMetaType.Type.Double, '', 4, 2))
            fields.append(QgsField('xtd_stb_nm', QMetaType.Type.Double, '', 4, 2))
        fields.append(QgsField('notes', QMetaType.Type.QString, '', 0, 0))

        # creating feature sink
        feedback.pushConsoleInfo(self.tr('Creating feature sink...'))
        (sink, dest_id) = self.parameterAsSink(parameters, self.OUTPUT, context, fields, geom_type, crs)
        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        # make variables accessible for post-processing
        self.file_type = file_type
        self.output = dest_id

        result = {self.OUTPUT: self.output}

        return result

    def postProcessAlgorithm(self, context, feedback):
        # get layer from source and context
        planning_layer = QgsProcessingUtils.mapLayerFromString(self.output, context)

        if self.file_type == 0:
            style = self.style_planning_points
            style_name = 'Cruise Tools Point Planning'
            style_desc = 'Point Planning style for QGIS Symbology from Cruise Tools plugin'
        elif self.file_type == 1:
            style = self.style_planning_lines
            style_name = 'Cruise Tools Line Planning'
            style_desc = 'Line Planning style for QGIS Symbology from Cruise Tools plugin'

        # loading Cruise Tools Planning style from QML style file
        feedback.pushConsoleInfo(self.tr('Loading style...'))
        planning_layer.loadNamedStyle(str(style))

        # writing style to GPKG (or else)
        feedback.pushConsoleInfo(self.tr('Writing style to output...\n'))
        planning_layer.saveStyleToDatabaseV2(name=style_name, description=style_desc, useAsDefault=True,
                                             uiFileContent=None)

        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Planning file created!\n'))

        result = {self.OUTPUT: self.output}

        return result

    def name(self):
        return 'createplanningfile'

    def icon(self):
        return QIcon(str(self.plugin_dir / 'icons' / 'create_planning_file.png'))

    def displayName(self):
        return self.tr('Create Planning File')

    def group(self):
        return self.tr('Planning')

    def groupId(self):
        return 'planning'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):
        doc = Path(self.plugin_dir) / 'doc' / 'create_planning_file.help'
        if not doc.is_file():
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):
        return CreatePlanningFile()
