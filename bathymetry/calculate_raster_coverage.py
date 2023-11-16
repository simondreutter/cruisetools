import os
import processing

from qgis.core import (
    QgsGeometry,
    QgsDistanceArea,
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterBand,
    QgsProcessingParameterFileDestination,
    QgsUnitTypes
)

from qgis.PyQt.QtCore import QCoreApplication
from PyQt5.QtGui import QIcon

from .bathymetry import Bathymetry
from .. import utils

class CalculateRasterCoverage(QgsProcessingAlgorithm, Bathymetry):
    """Calculate Raster Coverage."""
    
    # Processing parameters
    # inputs:
    INPUT = 'INPUT'
    BAND = 'BAND'
    # outputs:
    RASTER_AREA_KM2 = 'RASTER_AREA_KM2'
    DATA_COVERAGE_KM2 = 'DATA_COVERAGE_KM2'
    DATA_COVERAGE_M2 = 'DATA_COVERAGE_M2'
    DATA_COVERAGE_PERCENT = 'DATA_COVERAGE_PERCENT'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        """Initialize CalculateRasterCoverage."""
        super(CalculateRasterCoverage, self).__init__()
        
        # area of Bremen in km^2
        self.bremen_area = 419.4

    def initAlgorithm(self, config=None):  # noqa
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                name=self.INPUT,
                description=self.tr('Input Raster Layer'),
                defaultValue=None,
                optional=False)
        )
        self.addParameter(
            QgsProcessingParameterBand(
                name=self.BAND,
                description=self.tr('Band Number'),
                defaultValue=1,
                parentLayerParameterName=self.INPUT,
                optional=False,
                allowMultiple=False)
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                name=self.OUTPUT,
                description=self.tr('Statistics'),
                fileFilter='TXT (*.txt)',
                defaultValue=None,
                optional=True,
                createByDefault=False)
        )

    def processAlgorithm(self, parameters, context, feedback):  # noqa
        # get input variables
        raster_layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        band_number = self.parameterAsInt(parameters, self.BAND, context)
        output = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        
        # layer name
        name = raster_layer.name()
        
        # layer provider
        provider = raster_layer.dataProvider()
        
        # get CRS
        crs_raster = raster_layer.crs()
        
        # set project ellipsoid (for measurements) to CRS ellipsoid
        ellipsoid = context.project().crs().ellipsoidAcronym()
        
        # get transform context from project
        trans_context = context.project().transformContext()
        
        # 5% done
        feedback.setProgress(5)
        
        # Initialize Area calculator class with ellipsoid
        da = QgsDistanceArea()
        da.setSourceCrs(crs_raster, trans_context)
        da.setEllipsoid(ellipsoid)
        
        # get raster extent
        extent = raster_layer.extent()
        extent = QgsGeometry().fromRect(extent)
        
        # 20% done
        feedback.setProgress(20)
        
        # get area of extent
        feedback.pushConsoleInfo(self.tr('Measuring area of raster rectangle...'))
        area = da.measureArea(extent)
        
        # convert area
        area_m2 = da.convertAreaMeasurement(area, QgsUnitTypes.AreaSquareMeters)
        
        # 30% done
        feedback.setProgress(30)
        
        # check if NoData value is set
        if provider.sourceHasNoDataValue(band_number):
            feedback.pushConsoleInfo(self.tr('Calculating NoData percentage...'))
            # unique values parameters
            rastervalue_params = {'INPUT': raster_layer,
                                  'BAND': band_number}
            
            # run unique values
            result = processing.run('native:rasterlayeruniquevaluesreport', rastervalue_params)
            
            # get total pixel and nodata count
            cells = result['TOTAL_PIXEL_COUNT']
            nodata_cells = result['NODATA_PIXEL_COUNT']
            
            # calculate nodata percentage
            nodata_percentage = nodata_cells / cells
            
            # calclate data coverage
            feedback.pushConsoleInfo(self.tr('Calculating data coverage...\n'))
            coverage_m2 = area_m2 * (1 - nodata_percentage)
            coverage_percentage = (1 - nodata_percentage)
        else:
            feedback.reportError(self.tr('Missing NoData value(s) detected. Check settings of the raster layer!'), fatalError=False)
            coverage_m2 = area_m2
            coverage_percentage = 1.0
        
        # 80% done
        feedback.setProgress(80)
        
        # calculate area units
        area_km2 = area_m2 / (1000 * 1000)
        coverage_km2 = coverage_m2 / (1000 * 1000)
        
        feedback.pushConsoleInfo(self.tr('------------------------------------------\n'))
        
        feedback.pushConsoleInfo(self.tr(f'Raster Coverage of Layer [ {name} ]:\n'))
        
        feedback.pushConsoleInfo(self.tr(f'Raster Area [km2] ....... : {round(area_km2, 3)}'))
        feedback.pushConsoleInfo(self.tr(f'Data Coverage [km2] ..... : {round(coverage_km2, 3)}'))
        feedback.pushConsoleInfo(self.tr(f'Data Coverage [m2] ...... : {round(coverage_m2, 2)}'))
        feedback.pushConsoleInfo(self.tr(f'Data Coverage [%] ....... : {round(coverage_percentage * 100, 2)}\n'))
        
        feedback.pushConsoleInfo(self.tr(f'This is {round(coverage_km2 / self.bremen_area, 2)} times the area of Bremen\n'))
        
        feedback.pushConsoleInfo(self.tr('------------------------------------------\n'))
        
        # 100% done
        feedback.setProgress(100)
        feedback.pushInfo(self.tr(f'{utils.return_success()}! Raster area has been calculated!\n'))
        
        result = {self.RASTER_AREA_KM2 : area_km2,
                  self.DATA_COVERAGE_KM2 : coverage_km2,
                  self.DATA_COVERAGE_M2 : coverage_m2,
                  self.DATA_COVERAGE_PERCENT : coverage_percentage,
                  self.OUTPUT : output}
        
        if output != '':
            self.write_output(name, result, output)
        
        return result

    def write_output(self, name, result, output):
        """Write output to TXT file.

        Parameters
        ----------
        name : str
            raster layer name
        result : dict
            result dictionary
        output : str
            file path to output file

        """
        area_km2 = result[self.RASTER_AREA_KM2]
        coverage_km2 = result[self.DATA_COVERAGE_KM2]
        coverage_m2 = result[self.DATA_COVERAGE_M2]
        coverage_percentage = result[self.DATA_COVERAGE_PERCENT]
        content = f'''Raster Coverage of Layer [ {name} ]:

Raster Area [km2]:     {round(area_km2, 3)}
Data Coverage [km2]:   {round(coverage_km2, 3)}
Data Coverage [m2]:    {round(coverage_m2, 2)}
Data Coverage [%]:     {round(coverage_percentage * 100, 2)}

This is {round(coverage_km2 / self.bremen_area, 2)} times the area of Bremen

'''
        with open(output, 'w') as f:
            f.write(content)

    def name(self):  # noqa
        return 'calculaterastercoverage'

    def icon(self):  # noqa
        icon = QIcon(f'{self.plugin_dir}/icons/calculate_raster_coverage.png')
        return icon

    def displayName(self):  # noqa
        return self.tr('Calculate Raster Coverage')

    def group(self):  # noqa
        return self.tr('Bathymetry')

    def groupId(self):  # noqa
        return 'bathymetry'

    def tr(self, string):  # noqa
        return QCoreApplication.translate('Processing', string)

    def shortHelpString(self):  # noqa
        doc = f'{self.plugin_dir}/doc/calculate_raster_coverage.help'
        if not os.path.exists(doc):
            return ''
        with open(doc) as helpf:
            help = helpf.read()
        return help

    def createInstance(self):  # noqa
        return CalculateRasterCoverage()
