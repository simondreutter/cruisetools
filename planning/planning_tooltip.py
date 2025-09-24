from math import pi

from PyQt5.QtCore import QObject, QEvent, Qt
from PyQt5.QtWidgets import QToolTip

from qgis.core import Qgis
from qgis.core import QgsProject
from qgis.core import QgsDistanceArea
from qgis.core import QgsGeometry
from qgis.core import QgsPointXY
from qgis.core import QgsCoordinateTransform

from qgis.gui import QgsMapToolAdvancedDigitizing
from qgis.gui import QgsMapToolDigitizeFeature

from qgis.utils import iface


class LinePlanningToolTip(QObject):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.layer = canvas.currentLayer()
        self.map_tool = self.canvas.mapTool()

        # Init counter
        self.edit_vetex = False
        self.click_counter = 0

        # Define measuring tool
        self.distArea = QgsDistanceArea()
        self.distArea.setEllipsoid(QgsProject.instance().ellipsoid())  # match project ellipsoid
        self.distArea.setSourceCrs(self.layer.crs(), QgsProject.instance().transformContext())
        self.checkEllipsoid()

        # Define CRS transform (project -> layer)
        self.transform_map2layer = QgsCoordinateTransform(QgsProject.instance().crs(), self.layer.crs(),
                                                          QgsProject.instance().transformContext())

        # Init variables
        self.point_start = None
        self.distance_m = None
        self.speed_kn = None
        self.field_speed = 'speed_kn'

        # Install event filter on the canvas viewport
        self.canvas.viewport().installEventFilter(self)

    def checkEllipsoid(self):
        """Check whether project ellipsoid for measurements is set."""
        ellipsoid_distArea = QgsProject.instance().ellipsoid()
        ellipsoid_crs = QgsProject.instance().crs().ellipsoidAcronym()
        if ellipsoid_distArea != ellipsoid_crs:
            iface.messageBar().pushMessage(
                'Cruise Tools',
                'Project ellipsoid for distance calculations is not set! Please consider configuring a ellipsoid matching the project CRS (Project > Properties... > General > Ellipsoid)',
                level=Qgis.Warning,
                duration=8
            )

    def eventFilter(self, obj, event):
        """Listen to events.

        Parameters
        ----------
        obj : QObject
            The object that received the event.
        event : QEvent
            The event being processed

        Returns
        -------
        bool
            True if the event was handled (and should stop propagating),
            False otherwise.

        """
        if event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                self.map_tool = self.canvas.mapTool()
                self.layer = self.canvas.currentLayer()

                # (1) Add new feature
                if isinstance(self.map_tool, QgsMapToolDigitizeFeature) and self.map_tool.toolName() == 'Add feature':
                    # print('[DEBUG] Add new feature')
                    self.get_new_point(event)
                    return False

                # (2) Edit feature (using Vertex Tool)
                elif isinstance(self.map_tool, QgsMapToolAdvancedDigitizing) and self.map_tool.toolName() == '':
                    if self.click_counter == 1:
                        self.reset()
                        return True
                    # print('[DEBUG] Edit feature')
                    self.edit_vertex = True
                    self.click_counter += 1
                    self.get_reference_point(event)
                    return False

            elif event.button() == Qt.RightButton:
                self.reset()
                return True

        elif event.type() == QEvent.MouseMove:
            self.updateToolTip(event)
            return False

        elif event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Escape:
                self.reset()
                return True

        return False

    def get_reference_point(self, event):
        """Select reference point (when editing vertex).

        Parameters
        ----------
        event : QMouseEvent
            Mouse event containing the clicked position

        """
        point_click = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
        geom_point_click = QgsGeometry.fromPointXY(point_click)
        # print(f'[DEBUG] {geom_point_click = }')

        # Get all features
        features = list(self.layer.getFeatures())

        # Find nearest line feature from layer
        feat_nearest = None
        dist_nearest = float('inf')
        for f in features:
            dist = f.geometry().distance(geom_point_click)
            if dist < dist_nearest:
                feat_nearest = f
                dist_nearest = dist
        # print(f'[DEBUG] {feat_nearest = }')
        # print(f'[DEBUG] {dist_nearest = }')
        if feat_nearest:
            # Get line geometry
            geom = feat_nearest.geometry()

            # Get closest vertex from active line feature
            vertex, idx_close, idx_prev, idx_next, _ = geom.closestVertex(point_click)
            if idx_close == 0:
                idx_prev = idx_next
            # print(f'[DEBUG] {vertex = }')
            # print(f'[DEBUG] {idx_close = } {idx_prev = } {idx_next = }')

            # Set reference (start) point
            self.point_start = QgsPointXY(geom.vertexAt(idx_prev))
            # print(f'[DEBUG] {self.point_start = }')

            # Get feature fields
            fields = feat_nearest.fields()

            speed_kn = feat_nearest[self.field_speed]
            # print(f'[DEBUG] {speed_kn = }')
            if speed_kn:
                self.speed_kn = speed_kn
        else:
            print(f'[ERROR] Cannot find nearest feature for layer < {self.layer.name()} >!')

    def get_new_point(self, event):
        """Select reference point (when adding feature).

        Parameters
        ----------
        event : QMouseEvent
            Mouse event containing the clicked position

        """
        point = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
        point = self.transform_map2layer.transform(point)
        self.point_start = QgsPointXY(point)

    def calc_duration(self, distance_m: float = None, speed_kn: float = None):
        """Calculate time duration using distance (meter) and ship's speed (knots).

        Parameters
        ----------
        distance_m : float, optional
            Distance in meters. If None, uses self.distance_m
        speed_kn : float, optional
            Speed in knots. If None, uses self.speed_kn

        Returns
        -------
        str
            Duration formatted as ``hh:mm:ss``

        """
        if distance_m is None:
            distance_m = self.distance_m
        if speed_kn is None:
            speed_kn = self.speed_kn

        # Convert knots to m/s
        speed = speed_kn * 0.514444

        # Calculate total time (in seconds)
        total_seconds = int(distance_m / speed)

        # Convert to hh:mm:ss
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f'{hours:02d}:{minutes:02d}:{seconds:02d}'

    def updateToolTip(self, event):
        """Update canvas ToolTip with current distance, heading, and time.

        Parameters
        ----------
        event : QMouseEvent
            Mouse move event providing the current cursor position

        """
        if not self.point_start:
            return

        point_cursor = self.canvas.getCoordinateTransform().toMapCoordinates(event.pos())
        point_cursor = self.transform_map2layer.transform(point_cursor)
        # print(f'[DEBUG]    {self.point_start = }   {point_cursor = }')
        distance = self.distArea.measureLine(self.point_start, point_cursor)
        self.distance_m = self.distArea.convertLengthMeasurement(distance, Qgis.DistanceUnit.Meters)
        distance_nm = self.distArea.convertLengthMeasurement(distance, Qgis.DistanceUnit.NauticalMiles)

        bearing = self.distArea.bearing(self.point_start, point_cursor) * 180 / pi
        bearing = bearing + 360 if bearing < 0 else bearing

        txt = f'{self.distance_m:,.0f} m; {distance_nm:.3f} NM; {bearing:.1f}°'
        if self.speed_kn:
            duration = self.calc_duration()
            txt += f'\n{duration} @ {self.speed_kn:g} kn'
        QToolTip.showText(self.canvas.mapToGlobal(event.pos()), txt, self.canvas)

    def reset(self):
        """Reset the internal state of the tool."""
        # print('[DEBUG] Reset')
        self.click_counter = 0
        self.distance_m = None
        self.point_start = None
