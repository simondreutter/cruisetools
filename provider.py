# -*- coding: utf-8 -*-
import os
from qgis.core import QgsProcessingProvider
from PyQt5.QtGui import QIcon

from .bathymetry import LoadBathymetry
from .bathymetry import CalculateRasterCoverage
from .bathymetry import ExportShadedBathymetry
from .contour import CreateContours
from .vector import WritePointCoordinates
from .vector import WriteLineLength
from .vector import WritePolygonArea
from .vector import CreateCoordinateGrid
from .vector import SwapVectors
from .planning import CreatePlanningFile
from .planning import PlanningLinesToVertices
from .planning import EstimateMBESCoverage
from .planning import ExportToBridge

class CruiseToolsProvider(QgsProcessingProvider):
    def unload(self):
        QgsProcessingProvider.unload(self)

    def loadAlgorithms(self):
        self.addAlgorithm(LoadBathymetry())
        self.addAlgorithm(CalculateRasterCoverage())
        self.addAlgorithm(ExportShadedBathymetry())
        self.addAlgorithm(CreateContours())
        self.addAlgorithm(WritePointCoordinates())
        self.addAlgorithm(WriteLineLength())
        self.addAlgorithm(WritePolygonArea())
        self.addAlgorithm(CreateCoordinateGrid())
        self.addAlgorithm(SwapVectors())
        self.addAlgorithm(CreatePlanningFile())
        self.addAlgorithm(PlanningLinesToVertices())
        self.addAlgorithm(EstimateMBESCoverage())
        self.addAlgorithm(ExportToBridge())

    def icon(self):
        icon = QIcon(os.path.dirname(__file__) + '/icons/icon.png')
        return icon

    def id(self):
        return 'cruisetools'

    def name(self):
        return 'Cruise Tools'

    def longName(self):
        return self.name()
