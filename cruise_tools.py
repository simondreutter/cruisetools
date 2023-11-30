"""
/***************************************************************************
 CruiseTools
                                 A QGIS plugin
 The toolbox you need for marine research cruises (planning and stuff)!
                              -------------------
        begin                : 2019-06-12
        copyright            : (C) 2019 by Simon Dreutter & Fynn Warnke
        email                : simon.dreutter@awi.de / fynn.warnke@awi.de
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt5.QtCore import * # noqa
from PyQt5.QtGui import *  # noqa
from PyQt5.QtWidgets import *  # noqa

# Initialize Qt resources from file resources.py
from .resources import *  # noqa

# Import the code for the DockWidget
import os.path

# Import some tools
from qgis.core import *  # noqa
from qgis.gui import *  # noqa
from qgis.utils import *  # noqa
import processing

# Import Cruise Tools modules
from .provider import CruiseToolsProvider
from . import utils
from .logging import LogPosition

# Import GUI
from .gui.readme import ReadmeWindow
from .gui.log_position_settings import LogPositionSettings

class CruiseTools:  # noqa
    """QGIS Plugin - Cruise Tools"""
    
    def __init__(self, iface):  # noqa
        """Constructor.

        Parameters
        ----------
        iface : QgsInterface
            An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.

        """
        # Save reference to the QGIS interface
        self.iface = iface
        
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]  # noqa
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            f'CruiseTools_{locale}.qm'
        )
        
        if os.path.exists(locale_path):
            self.translator = QTranslator()  # noqa
            self.translator.load(locale_path)
            
            if qVersion() > '4.3.3':  # noqa
                QCoreApplication.installTranslator(self.translator)  # noqa
        
        # Declare instance attributes
        self.actions = []
        self.menu = self.tr('&Cruise Tools')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar('CruiseTools')
        self.toolbar.setObjectName('CruiseTools')
                
        #self.pluginIsActive = False
        self.dockwidget = None
        
        # plugin variables to store some user defaults at runtime
        self.mbes_coverage_raster = None
        
        self.provider = None
        
        self.posiview_enabled = False
        
        self.first_start = None
        
        self.settingsDialog = None
        self.shortcutsManager = None
        
        #self.config = config.CruiseToolsConfig()           # FIXME: DO WE NEED THIS?

    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        
        We implement this ourselves since we do not inherit QObject.

        Parameters
        ----------
        message : str, QString
            String for translation.

        Returns
        -------
        translation : str
            QCoreApplication.translate()

        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('CruiseTools', message)  # noqa

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None
    ):
        """Add a toolbar icon to the toolbar.

        Parameters
        ----------
        icon_path : str
            Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        text : str
            Text that should be shown in menu items for this action.
        callback : function
            Function to be called when the action is triggered.
        enabled_flag : bool
            A flag indicating if the action should be enabled
            by default. Defaults to True.
        add_to_menu : bool
            Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        add_to_toolbar : bool
            Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        status_tip : str
            Optional text to show in a popup when mouse pointer
            hovers over the action. (Default value = None)
        parent : QWidget
            Parent widget for the new action. Defaults None.
        whats_this :
            Optional text to show in the status bar when the
            mouse pointer hovers over the action. (Default value = None)

        Returns
        -------
        action : QAction

        """
        icon = QIcon(icon_path)  # noqa
        action = QAction(icon, text, parent)  # noqa
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        
        if status_tip is not None:
            action.setStatusTip(status_tip)
        
        if whats_this is not None:
            action.setWhatsThis(whats_this)
        
        if add_to_toolbar:
            self.toolbar.addAction(action)
        
        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)
        
        self.actions.append(action)
        
        return action

    def initProcessing(self):  # noqa
        # Add the processing provider
        self.provider = CruiseToolsProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)  # noqa

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        self.initProcessing()
        
        # get first start indication
        self.first_start = True
        
        icon_path = ':/plugins/cruisetools/icons'
        
        # README BUTTON
        icon = QIcon(f'{icon_path}/icon.png')  # noqa
        readme = self.add_action(
            icon,
            text=self.tr('Cruise Tools'),
            callback=self.run_readme,
            parent=self.iface.mainWindow()
        )
        readme.setToolTip('Cruise Tools README')
        readme.triggered.connect(self.check_posiview_plugin)
        
        # BATHYMETRY SUBMENU
        bathy_menu = QMenu()  # noqa
        # show tool tips
        bathy_menu.setToolTipsVisible(True)
        
        # load bathymetry button
        icon = QIcon(f'{icon_path}/load_bathymetry.png')  # noqa
        load_bathymetry = bathy_menu.addAction(icon, self.tr('Load Bathymetry'), self.run_load_bathymetry)
        load_bathymetry.setToolTip(
            'Load a bathymetry grid file (*.tif, *.nc) with pre defined style and hillshade.\n'
            'Change color ramp and depth scale in the Cruise Tools settings, or later in the\n'
            'layer symbology'
        )
        
        # export bathymetry button
        icon = QIcon(f'{icon_path}/export_shaded_bathymetry.png')  # noqa
        export_shaded_bathymetry = bathy_menu.addAction(icon, self.tr('Export Shaded Bathymetry'), self.run_export_shaded_bathymetry)
        export_shaded_bathymetry.setToolTip(
            'Export an RGB version of a loaded raster layer with set colorramp.\n'
            'and shaded by Hillshade, Slope or both.'
        )
        
        bathy_menu.addSeparator()
        
        # raster coverage button
        icon = QIcon(f'{icon_path}/calculate_raster_coverage.png')  # noqa
        calculate_raster_coverage = bathy_menu.addAction(icon, self.tr('Calculate Raster Coverage'), self.run_calculate_raster_coverage)
        calculate_raster_coverage.setToolTip('Calculate approximate coverage area of raster datasets.')
        
        # setup bathymetry menu
        icon = QIcon(f'{icon_path}/bathymetry_menu.png')  # noqa
        self.bathyAction = QAction(icon, 'Bathymetry', self.iface.mainWindow())  # noqa
        self.bathyAction.setMenu(bathy_menu)
        self.actions.append(self.bathyAction)  # required for proper unloading
        self.iface.addPluginToMenu(self.menu, self.bathyAction)  # add `bathy_menu` to menu (Plugins > Cruise Tools)
        
        self.bathyButton = QToolButton()  # noqa
        self.bathyButton.setMenu(bathy_menu)
        self.bathyButton.setDefaultAction(self.bathyAction)
        self.bathyButton.setPopupMode(QToolButton.InstantPopup)  # noqa
        self.transformToolbar = self.toolbar.addWidget(self.bathyButton)
        
        # CONTOURS BUTTON
        icon = f'{icon_path}/create_contours.png'
        create_contours = self.add_action(
            icon,
            text=self.tr('Create Contours'),
            callback=self.run_create_contours,
            parent=self.iface.mainWindow()
        )
        create_contours.setToolTip('Create nice contour lines.')
        
        # VECTOR SUBMENU
        vector_menu = QMenu()  # noqa
        # show tool tips
        vector_menu.setToolTipsVisible(True)
        
        # write point coordinates button
        icon = QIcon(f'{icon_path}/write_point_coordinates.png')  # noqa
        write_point_coordinates = vector_menu.addAction(
            icon,
            self.tr('Write Point Coordinates'),
            self.run_write_point_coordinates,
        )
        write_point_coordinates.setToolTip(
            'Add attributes to the selected point layer containing\n'
            'Latitude and Longitude in DD and DDM (EPSG:WGS84)\n'
            'and XY coordinates in a selected CRS (optional).'
        )
        
        # write line length button
        icon = QIcon(f'{icon_path}/write_line_length.png')  # noqa
        write_line_length = vector_menu.addAction(icon, self.tr('Write Line Length'), self.run_write_line_length)
        write_line_length.setToolTip(
            f'Add attributes to the selected line layer containing\n'
            f'length in meters and nautical miles\n\n'
            f'Measurements are ellipsoidal, based on Project\n'
            f'measurement ellispoid ({QgsProject.instance().crs().ellipsoidAcronym()}).'
        )
        
        # write polygon area button
        icon = QIcon(f'{icon_path}/write_polygon_area.png')  # noqa
        write_polygon_area = vector_menu.addAction(icon, self.tr('Write Polygon Area'), self.run_write_polygon_area)
        write_polygon_area.setToolTip(
            f'Add attributes to the selected polygon layer containing\n' # noqa
            f'area in square meters and square kilometers.\n\n'
            f'Measurements are ellipsoidal, based on Project\n'
            f'measurement ellispoid ({QgsProject.instance().crs().ellipsoidAcronym()}).'
        )
        
        vector_menu.addSeparator()
        
        # create coordinate grid button
        icon = QIcon(f'{icon_path}/create_coordinate_grid.png')  # noqa
        create_coordinate_grid = vector_menu.addAction(icon, self.tr('Create Coordinate Grid'), self.run_create_coordinate_grid)
        create_coordinate_grid.setToolTip(
            f'Create a geographic coordinate grid feature layer.'
        )
        
        vector_menu.addSeparator()
        
        # swap vectors button
        icon = QIcon(f'{icon_path}/swap_vectors.png')  # noqa
        swap_vectors = vector_menu.addAction(icon, self.tr('Swap Vectors'), self.run_swap_vectors)
        swap_vectors.setToolTip('Swap direction of selected line layer (for contour labels, etc.).')
        
        # setup vector menu
        icon = QIcon(f'{icon_path}/vector_menu.png')  # noqa
        self.vectorAction = QAction(icon, 'Vector', self.iface.mainWindow())  # noqa
        self.vectorAction.setMenu(vector_menu)
        self.actions.append(self.vectorAction)  # required for proper unloading
        self.iface.addPluginToMenu(self.menu, self.vectorAction)  # add `vector_menu` to menu (Plugins > Cruise Tools)
        
        self.vectorButton = QToolButton()  # noqa
        self.vectorButton.setMenu(vector_menu)
        self.vectorButton.setDefaultAction(self.vectorAction)
        self.vectorButton.setPopupMode(QToolButton.InstantPopup)  # noqa
        self.transformToolbar = self.toolbar.addWidget(self.vectorButton)
        
        # PLANNING SUBMENU
        planning_menu = QMenu()  # noqa
        # show tool tips
        planning_menu.setToolTipsVisible(True)
        
        # create point planning file button
        icon = QIcon(f'{icon_path}/create_planning_file.png')  # noqa
        create_planning_file = planning_menu.addAction(icon, self.tr('Create Planning File'), self.run_create_planning_file)
        create_planning_file.setToolTip('Create new layer file for point/line planning purposes.')
        
        # planning lines to vertices button
        icon = QIcon(f'{icon_path}/planning_lines_to_vertices.png')  # noqa
        planning_lines_to_vertices = planning_menu.addAction(icon, self.tr('Planning Lines to Vertices'), self.run_planning_lines_to_vertices)
        planning_lines_to_vertices.setToolTip('Extract vertices from planning line layer.')
        
        # parallel line planning
        icon = QIcon(f'{icon_path}/parallel_line_planning.png')  # noqa
        parallel_line_planning = planning_menu.addAction(icon, self.tr('Parallel Line Planning'), self.run_parallel_line_planning)
        parallel_line_planning.setToolTip('Plan parallel survey lines.')
        
        planning_menu.addSeparator()
        
        # estimate mbes coverage
        icon = QIcon(f'{icon_path}/estimate_mbes_coverage.png')  # noqa
        estimate_mbes_coverage = planning_menu.addAction(icon, self.tr('Estimate MBES Coverage'), self.run_estimate_mbes_coverage)
        estimate_mbes_coverage.setToolTip(
            'Estimate MBES coverage for a survey planning line.\n\n'
            'Survey settings can be set in the dialog.'
        )
        
        planning_menu.addSeparator()
        
        # export to bridge button
        icon = QIcon(f'{icon_path}/export_to_bridge.png')  # noqa
        export_to_bridge = planning_menu.addAction(icon, self.tr('Export to Bridge'), self.run_export_to_bridge)
        export_to_bridge.setToolTip('Export planning layer (point or line) to bridge exchange format.')
        
        # setup planning menu
        icon = QIcon(f'{icon_path}/planning_menu.png')  # noqa
        self.planningAction = QAction(icon, 'Planning', self.iface.mainWindow())  # noqa
        self.planningAction.setMenu(planning_menu)
        self.actions.append(self.planningAction)  # required for proper unloading
        self.iface.addPluginToMenu(self.menu, self.planningAction)  # add `planning_menu` to menu (Plugins > Cruise Tools)

        self.planningButton = QToolButton()  # noqa
        self.planningButton.setMenu(planning_menu)
        self.planningButton.setDefaultAction(self.planningAction)
        self.planningButton.setPopupMode(QToolButton.InstantPopup)  # noqa
        self.transformToolbar = self.toolbar.addWidget(self.planningButton)
        
        # LOGGING SUBMENU
        logging_menu = QMenu()  # noqa
        logging_menu.setToolTipsVisible(True)
        
        #icon = QIcon(':images/themes/default/propertyicons/system.svg')  # noqa
        icon = QIcon(':images/themes/default/processingAlgorithm.svg')
        self.logPositionSettings = logging_menu.addAction(
            icon, self.tr('Log Position settings'), self.run_log_position_settings,
        )
        self.logPositionSettings.setToolTip('Set settings for position logging')
        
        #icon = QIcon(':images/themes/default/cursors/mCapturePoint.svg')  # noqa
        icon = QIcon(f'{icon_path}/log_position.png')  # noqa
        self.logPosition = QAction(icon, 'Log Position', self.iface.mainWindow())  # noqa
        self.logPosition.hovered.connect(self.check_posiview_plugin)
        self.logPosition.triggered.connect(self.run_log_position)
        self.logPosition.setMenu(logging_menu)
        self.check_posiview_plugin(show_message=False)
        
        self.actions.append(self.logPosition)  # required for proper unloading
        self.iface.addPluginToMenu(self.menu, self.logPosition)  # add `planning_menu` to menu (Plugins > Cruise Tools)
        
        # create Toolbar button
        self.logPositionButton = QToolButton()
        self.logPositionButton.setDefaultAction(self.logPosition)
        self.transformToolbar = self.toolbar.addWidget(self.logPositionButton)
        
        # register keyboard shortcuts
        self.shortcutsManager = QgsGui.shortcutsManager()
        check_logPosition = self.shortcutsManager.registerAction(self.logPosition, 'F10')
        check_logPositionSettings = self.shortcutsManager.registerAction(self.logPositionSettings, 'Ctrl+F10')
        
    #===============================================================================

    def unload(self):
        """Remove the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr('&Cruise Tools'),
                action
            )
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
        
        # remove from processing toolbox
        QgsApplication.processingRegistry().removeProvider(self.provider)
        
        # remove shortcut
        check_logPosition = self.shortcutsManager.unregisterAction(self.logPosition)
        check_logPositionSettings = self.shortcutsManager.unregisterAction(self.logPositionSettings)

    #===============================================================================
    #=================================   README   ==================================
    #===============================================================================

    def run_readme(self):
        """Show README."""
        # load README.md
        with open(os.path.join(self.plugin_dir, 'README.md'), 'r') as f:
            readme_text = f.read()
        self.readme = ReadmeWindow(readme_text)
        self.readme.show()
        iface.messageBar().pushMessage('Cruise Tools ', 'Awesome and practical Cruise Tools by the Bauernprogrammiererz Fynn & Simon! <3', level=Qgis.Info)
        return

    #===============================================================================
    #===============================   BATHYMETRY   ================================
    #===============================================================================

    def run_load_bathymetry(self):
        """Run LoadBathymetry module."""
        result = processing.execAlgorithmDialog('cruisetools:loadbathymetry', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Grid loaded successfully!', level=Qgis.Success)
        return

    def run_export_shaded_bathymetry(self):
        """Run ExportShadedBathymetry module."""
        result = processing.execAlgorithmDialog('cruisetools:exportshadedbathymetry', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Shaded bathymetry file is created: {utils.return_file_link(result["OUTPUT"])}', level=Qgis.Success)
        return

    def run_calculate_raster_coverage(self):
        """Run CalculateRasterCoverage module."""
        result = processing.execAlgorithmDialog('cruisetools:calculaterastercoverage', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Raster area has been calculated!', level=Qgis.Success)
        return

    #===============================================================================
    #================================   CONTOURS   =================================
    #===============================================================================

    def run_create_contours(self):
        """Run CreateContours module."""
        result = processing.execAlgorithmDialog('cruisetools:createcontours', {})
        if not result == {}:
            iface.activeLayer().setSubsetString('"length_m" > 1000')
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Contours have been computed: {utils.return_file_link(result["OUTPUT"])}', level=Qgis.Success)
        return

    #===============================================================================
    #=================================   VECTOR   ==================================
    #===============================================================================

    def run_write_point_coordinates(self):
        """Run WritePointCoordinates module."""
        result = processing.execAlgorithmDialog('cruisetools:writepointcoordinates', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Coordinates are in!', level=Qgis.Success)
        return

    def run_write_line_length(self):
        """Run WriteLineLength module."""
        result = processing.execAlgorithmDialog('cruisetools:writelinelength', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Lengths are in!', level=Qgis.Success)
        return

    def run_write_polygon_area(self):
        """Run WritePolygonArea module."""
        result = processing.execAlgorithmDialog('cruisetools:writepolygonarea', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Areas are in!', level=Qgis.Success)
        return

    def run_create_coordinate_grid(self):
        """Run CreateCoordinateGrid module."""
        result = processing.execAlgorithmDialog('cruisetools:createcoordinategrid', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Coordinate grid file created!', level=Qgis.Success)
        return

    def run_swap_vectors(self):
        """Run SwapVectors module."""
        result = processing.execAlgorithmDialog('cruisetools:swapvectors', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Vectors swapped successfully!', level=Qgis.Success)
        return

    #===============================================================================
    #================================   PLANNING   =================================
    #===============================================================================

    def run_create_planning_file(self):
        """Run CreatePlanningFile module."""
        result = processing.execAlgorithmDialog('cruisetools:createplanningfile', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Point planning file: {utils.return_file_link(result["OUTPUT"])}', level=Qgis.Success)
        return

    def run_planning_lines_to_vertices(self):
        """Run PlanningLinesToVertices module."""
        result = processing.execAlgorithmDialog('cruisetools:planninglinestovertices', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Line vertices file: {utils.return_file_link(result["OUTPUT"])}', level=Qgis.Success)
        return

    def run_parallel_line_planning(self):
        """Run ParallelLinePlanning module."""
        result = processing.execAlgorithmDialog('cruisetools:parallellineplanning', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Parallel lines have been planned!', level=Qgis.Success)
        return

    def run_estimate_mbes_coverage(self):
        """Run EstimateMBESCoverage module."""
        result = processing.execAlgorithmDialog('cruisetools:estimatembescoverage', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! MBES coverage has been estimated: {utils.return_file_link(result["OUTPUT"])}', level=Qgis.Success)
        return

    def run_export_to_bridge(self):
        """Run ExportToBridge module."""
        result = processing.execAlgorithmDialog('cruisetools:exporttobridge', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Exported file: {utils.return_file_link(result["OUTPUT"])}', level=Qgis.Success)
        return

    #===============================================================================
    #================================   LOGGING   ==================================
    #===============================================================================

    def check_posiview_plugin(self, show_message: bool = True):
        """Check availability of PosiView plugin."""
        self.posiview_enabled = False
        
        # get PosiView reference from loaded plugins
        self.posiview = plugins.get('PosiView', None)
        
        if self.posiview is not None:
            # get PosiView Project
            self.posiview_project = self.posiview.project
            
            # cheap check if PosiView Project is already loaded
            if self.posiview_project.dataProviders != {}:
                self.posiview_enabled = True
        
        if not self.posiview_enabled and show_message:
            self.iface.messageBar().pushMessage(
                'Log Position',
                'PosiView Plugin is not enabled! Please enable and start tracking in order to use "Log Position".',
                level=Qgis.Info,
                duration=3
            )
        
        self.logPosition.setEnabled(self.posiview_enabled)
        # print('[Cruise Tools]    self.posiview_enabled:', self.posiview_enabled)
    
    def run_log_position_settings(self):
        """Run LogPositionSettings module."""
        if self.first_start is True:
            # print('[SETTINGS]    self.first_start:', self.first_start)  # TODO
            # init LogPosition class (only ONCE!)
            self.log_position_class = LogPosition(self.first_start)
            self.first_start = False
        
        # update PosiView devices
        self.log_position_class.update_devices()
        
        # display Settings dialog
        self.log_position_class.show()
            
    def run_log_position(self):
        """Run LogPosition module."""
        # check for PosiView Plugin
        self.check_posiview_plugin()
        
        if self.posiview_project.trackingStarted:
            if self.first_start:  # FIXME
                # print('[LOGGING]    self.first_start:', self.first_start)
                widget = self.iface.messageBar().createMessage(
                    'Setup Log Position', 'Set settings before starting to log positions.',
                )
                button = QPushButton()
                button.setText('Log Position settings')
                button.pressed.connect(self.run_log_position_settings)
                widget.layout().addWidget(button)
                
                # show message
                iface.messageBar().pushWidget(widget, Qgis.Warning, duration=5)
                
                # [DEBUGGING]
                # self.log_position_class = LogPosition(self.first_start)
                # self.first_start = False
            else:
                # log position
                self.log_position_class.log_position()
                
                self.iface.messageBar().pushMessage(
                    'Log Position',
                    f'Logged current position and saved to selected layer <{self.log_position_class.layer_logging.name()}>',
                    level=Qgis.Info,
                    duration=2
                )
        else:
            self.iface.messageBar().pushMessage(
                'Log Position',
                'PosiView Plugin is not tracking! Please start tracking in order to use "Log Position".',
                level=Qgis.Critical,
                duration=3
            )
