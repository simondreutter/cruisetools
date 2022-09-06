# -*- coding: utf-8 -*-
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
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# Initialize Qt resources from file resources.py
from .resources import *

# Import the code for the DockWidget
import os.path

# Import some tools
from qgis.core import *
from qgis.gui import *
from qgis.utils import *
import processing

# Import Cruise Tools modules
from .provider import CruiseToolsProvider
from . import utils

# Import GUI
from .gui.readme import ReadmeWindow

class CruiseTools:
    """QGIS Plugin - Cruise Tools"""
    def __init__(self, iface):
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
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            f'CruiseTools_{locale}.qm')
        
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            
            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
        
        # Declare instance attributes
        self.actions = []
        self.menu = self.tr('&Cruise Tools')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar('CruiseTools')
        self.toolbar.setObjectName('CruiseTools')
        
        #print "** INITIALIZING CruiseTools"
        
        #self.pluginIsActive = False
        self.dockwidget = None
        
        # plugin variables to store some user defaults at runtime
        self.mbes_coverage_raster = None
        
        self.provider = None
        
        #self.config = config.CruiseToolsConfig()           <<< DO WE NEED THIS?

    # noinspection PyMethodMayBeStatic
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
        return QCoreApplication.translate('CruiseTools', message)

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
        parent=None):
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
        
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
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

    def initProcessing(self):
        # Add the processing provider
        self.provider = CruiseToolsProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        self.initProcessing()
        
        # get first start indication
        self.first_start = True 
        
        icon_path = ':/plugins/cruisetools/icons'
        
        # README BUTTON
        icon = QIcon(f'{icon_path}/icon.png')
        readme = self.add_action(icon,
                                    text=self.tr('Cruise Tools'),
                                    callback=self.run_readme,
                                    parent=self.iface.mainWindow())
        readme.setToolTip('Show Cruise Tools README for information and instructions.')
        
        
        # BATHYMETRY SUBMENU
        bathy_menu = QMenu()
        # show tool tips
        bathy_menu.setToolTipsVisible(True)
        
        # load bathymetry button
        icon = QIcon(f'{icon_path}/load_bathymetry.png')
        load_bathymetry = bathy_menu.addAction(icon,self.tr('Load Bathymetry'), self.run_load_bathymetry)
        load_bathymetry.setToolTip('Load a bathymetry grid file (*.tif, *.nc) with pre defined style and hillshade.\n'
                                   'Change color ramp and depth scale in the Cruise Tools settings, or later in the\n'
                                   'layer symbology')
        
        # export bathymetry button
        icon = QIcon(f'{icon_path}/export_shaded_bathymetry.png')
        export_shaded_bathymetry = bathy_menu.addAction(icon,self.tr('Export Shaded Bathymetry'), self.run_export_shaded_bathymetry)
        export_shaded_bathymetry.setToolTip('Export an RGB version of a loaded raster layer with set colorramp.\n'
                                            'and shaded by Hillshade, Slope or both.')
        
        bathy_menu.addSeparator()
        
        # raster coverage button
        icon = QIcon(f'{icon_path}/calculate_raster_coverage.png')
        calculate_raster_coverage = bathy_menu.addAction(icon,self.tr('Calculate Raster Coverage'), self.run_calculate_raster_coverage)
        calculate_raster_coverage.setToolTip('Calculate approximate coverage area of raster datasets.')
        
        # setup bathymetry menu
        icon = QIcon(f'{icon_path}/bathymetry_menu.png')
        self.bathyAction = QAction(icon, 'Bathymetry', self.iface.mainWindow())
        self.bathyAction.setMenu(bathy_menu)
        
        self.bathyButton = QToolButton()
        self.bathyButton.setMenu(bathy_menu)
        self.bathyButton.setDefaultAction(self.bathyAction)
        self.bathyButton.setPopupMode(QToolButton.InstantPopup)
        self.tranformToolbar = self.toolbar.addWidget(self.bathyButton)
        
        # CONTOURS BUTTON
        icon = f'{icon_path}/create_contours.png'
        create_contours = self.add_action(icon,
                                    text=self.tr('Create Contours'),
                                    callback=self.run_create_contours,
                                    parent=self.iface.mainWindow())
        create_contours.setToolTip('Create nice contour lines.')
        
        # VECTOR SUBMENU
        vector_menu = QMenu()
        # show tool tips
        vector_menu.setToolTipsVisible(True)
        
        # write point coordinates button
        icon = QIcon(f'{icon_path}/write_point_coordinates.png')
        write_point_coordinates = vector_menu.addAction(icon,self.tr('Write Point Coordinates'), self.run_write_point_coordinates)
        write_point_coordinates.setToolTip('Add attributes to the selected point layer containing\n'
                                           'Latitude and Longitude in DD and DDM (EPSG:WGS84)\n'
                                           'and XY coordinates in a selected CRS (optional).')
        
        # write line length button
        icon = QIcon(f'{icon_path}/write_line_length.png')
        write_line_length = vector_menu.addAction(icon,self.tr('Write Line Length'), self.run_write_line_length)
        write_line_length.setToolTip(f'Add attributes to the selected line layer containing\n'
                                     f'length in meters and nautical miles\n\n'
                                     f'Measurements are ellipsoidal, based on Project\n'
                                     f'measurement ellispoid ({QgsProject.instance().crs().ellipsoidAcronym()}).')
        
        # write polygon area button
        icon = QIcon(f'{icon_path}/write_polygon_area.png')
        write_polygon_area = vector_menu.addAction(icon,self.tr('Write Polygon Area'), self.run_write_polygon_area)
        write_polygon_area.setToolTip(f'Add attributes to the selected polygon layer containing\n'
                                      f'area in square meters and square kilometers.\n\n'
                                      f'Measurements are ellipsoidal, based on Project\n'
                                      f'measurement ellispoid ({QgsProject.instance().crs().ellipsoidAcronym()}).')
        
        # swap vectors button
        icon = QIcon(f'{icon_path}/swap_vectors.png')
        swap_vectors = vector_menu.addAction(icon,self.tr('Swap Vectors'), self.run_swap_vectors)     
        swap_vectors.setToolTip('Swap direction of selected line layer (for contour labels, etc.).')
        
        # setup vector menu
        icon = QIcon(f'{icon_path}/vector_menu.png')
        self.vectorAction = QAction(icon, 'Vector', self.iface.mainWindow())
        self.vectorAction.setMenu(vector_menu)
        
        self.vectorButton = QToolButton()
        self.vectorButton.setMenu(vector_menu)
        self.vectorButton.setDefaultAction(self.vectorAction)
        self.vectorButton.setPopupMode(QToolButton.InstantPopup)
        self.tranformToolbar = self.toolbar.addWidget(self.vectorButton)
        
        # PLANNING SUBMENU
        planning_menu = QMenu()
        # show tool tips
        planning_menu.setToolTipsVisible(True)
        
        # create point planning file button
        icon = QIcon(f'{icon_path}/create_planning_file.png')
        create_planning_file = planning_menu.addAction(icon,self.tr('Create Planning File'), self.run_create_planning_file)
        create_planning_file.setToolTip('Create new layer file for point/line planning purposes.')
        
        # planning lines to vertices button
        icon = QIcon(f'{icon_path}/planning_lines_to_vertices.png')
        planning_lines_to_vertices = planning_menu.addAction(icon,self.tr('Planning Lines to Vertices'), self.run_planning_lines_to_vertices)
        planning_lines_to_vertices.setToolTip('Extract vertices from planning line layer.')
        
        planning_menu.addSeparator()
        
        # estimate mbes coverage
        icon = QIcon(f'{icon_path}/estimate_mbes_coverage.png')
        planning_lines_to_vertices = planning_menu.addAction(icon,self.tr('Estimate MBES Coverage'), self.run_estimate_mbes_coverage)
        planning_lines_to_vertices.setToolTip('Estimate MBES coverage for a survey planning line.\n\n'
                                              'Survey settings can be set in the dialog.')
        
        planning_menu.addSeparator()
        
        # export to bridge button
        icon = QIcon(f'{icon_path}/export_to_bridge.png')
        export_to_bridge = planning_menu.addAction(icon,self.tr('Export to Bridge'), self.run_export_to_bridge)
        export_to_bridge.setToolTip('Export planning layer (point or line) to bridge exchange format.')
        
        # setup planning menu
        icon = QIcon(f'{icon_path}/planning_menu.png')
        self.planningAction = QAction(icon, 'Planning', self.iface.mainWindow())
        self.planningAction.setMenu(planning_menu)
        
        self.planningButton = QToolButton()
        self.planningButton.setMenu(planning_menu)
        self.planningButton.setDefaultAction(self.planningAction)
        self.planningButton.setPopupMode(QToolButton.InstantPopup)
        self.tranformToolbar = self.toolbar.addWidget(self.planningButton)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        
        #print "** UNLOAD CruiseTools"
        
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr('&Cruise Tools'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar
        
        # remove from processing toolbox
        QgsApplication.processingRegistry().removeProvider(self.provider)

#===============================================================================
#=================================   README   ==================================
#===============================================================================

    def run_readme(self):
        """Show README"""
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
        """Run LoadBathymetry module"""
        result = processing.execAlgorithmDialog('cruisetools:loadbathymetry', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Grid loaded successfully!', level=Qgis.Success)
        return

    def run_export_shaded_bathymetry(self):
        """Run ExportShadedBathymetry module"""
        result = processing.execAlgorithmDialog('cruisetools:exportshadedbathymetry', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Shaded bathymetry file is created: {utils.return_file_link(result["OUTPUT"])}', level=Qgis.Success)
        return

    def run_calculate_raster_coverage(self):
        """Run CalculateRasterCoverage module"""
        result = processing.execAlgorithmDialog('cruisetools:calculaterastercoverage', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Raster area has been calculated!', level=Qgis.Success)
        return

#===============================================================================
#================================   CONTOURS   =================================
#===============================================================================

    def run_create_contours(self):
        """Run CreateContours module"""
        result = processing.execAlgorithmDialog('cruisetools:createcontours', {})
        if not result == {}:
            iface.activeLayer().setSubsetString('"length_m" > 1000')
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Contours have been computed: {utils.return_file_link(result["OUTPUT"])}', level=Qgis.Success)
        return

#===============================================================================
#=================================   VECTOR   ==================================
#===============================================================================

    def run_write_point_coordinates(self):
        """Run WritePointCoordinates module"""
        result = processing.execAlgorithmDialog('cruisetools:writepointcoordinates', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Coordinates are in!', level=Qgis.Success)
        return

    def run_write_line_length(self):
        """Run WriteLineLength module"""
        result = processing.execAlgorithmDialog('cruisetools:writelinelength', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Lengths are in!', level=Qgis.Success)
        return

    def run_write_polygon_area(self):
        """Run WritePolygonArea module"""
        result = processing.execAlgorithmDialog('cruisetools:writepolygonarea', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Areas are in!', level=Qgis.Success)
        return

    def run_swap_vectors(self):
        """Run SwapVectors module"""
        result = processing.execAlgorithmDialog('cruisetools:swapvectors', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Vectors swapped successfully!', level=Qgis.Success)
        return

#===============================================================================
#================================   PLANNING   =================================
#===============================================================================

    def run_create_planning_file(self):
        """Run CreatePlanningFile module"""
        result = processing.execAlgorithmDialog('cruisetools:createplanningfile', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Point Planning file: {utils.return_file_link(result["OUTPUT"])}', level=Qgis.Success)
        return

    def run_planning_lines_to_vertices(self):
        """Run PlanningLinesToVertices module"""
        result = processing.execAlgorithmDialog('cruisetools:planninglinestovertices', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Line Vertices file: {utils.return_file_link(result["OUTPUT"])}', level=Qgis.Success)
        return

    def run_estimate_mbes_coverage(self):
        """Run EstimateMBESCoverage module"""
        result = processing.execAlgorithmDialog('cruisetools:estimatembescoverage', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! MBES coverage has been estimated: {utils.return_file_link(result["OUTPUT"])}', level=Qgis.Success)
        return

    def run_export_to_bridge(self):
        """Run ExportToBridge module"""
        result = processing.execAlgorithmDialog('cruisetools:exporttobridge', {})
        if not result == {}:
            iface.messageBar().pushMessage('Cruise Tools ', f'{utils.return_success()}! Exported file: {utils.return_file_link(result["OUTPUT"])}', level=Qgis.Success)
        return
