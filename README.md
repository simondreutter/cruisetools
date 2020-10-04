# Cruise Tools
*v2.0 [Barents Sea]*

## Info
**The toolbox you need for marine research cruises (planning and stuff)!**  

    Authors :   Simon Dreutter & Fynn Warnke
    License :   Gnu GPL v3
    Email   :   simon.dreutter@awi.de / fynn.warnke@awi.de

Cruise Tools is a python plugin for QGIS (>3.10) that is supposed to fill a niche for cruise planning purposes. There are a handful of steps that we go through each time we extract coordinates for the bridge (DDM, not DD) or load a bathymetry grid (set color scale, hillshade, etc.) or similar. This is annoying and time consuming, hence, there needs to be a quicker way. This is what Cruise Tools was created for. It's supposed to create one (or two or three) click solutions to substitute 10 (or twenty or thirty) clicks.  
The toolbox is a work in progress, however, it’s functional and should be used along the way of development.

### Installation
Cruise Tools is now available via the QGIS plugin repository.
Open QGIS and go to `Plugins > Manage and Install Plugins` and activate `Cruise Tools` (tick it). If the Cruise Tools toolbar is not visible, right click on an open area on the toolbar and check Cruise Tools there as well.  
Sad side note: So far, Cruise Tools is developed on and for Windows only. It might work to some extend on a UNIX OS, but we never tested it. :/

## Bathymetry
### Load Bathymetry
You want to load a bathymetry (or topography) grid with hillshade and a nice color scale. Doing this manually takes about 1000 clicks (depending on how crazy your render settings are). Cruise Tools simply lets you select a grid file (`GeoTIFF` or `netCDF`), sets some color settings and overlays it with a hillshade that’s not just half transparently chucked on there like Ar\*GIS users tend to do, and adds everything into a handy sub group.  
You can adjust the color bar and min/max values in the dialog or later in the layer symbology.
___

### Export Shaded Bathymetry
While it's nice to view your (floating point) bathymetry in color and with an ad-hoc hillshade in QGIS, once in a while you need to have a colored and shaded RGB version of the grid for external applications of different sorts. To create this, the necessary procedure was usually very time consuming and awkward, so we built in a set of raster calculations that do the job for you. All you need to do is select a grid which has all colors set to your liking, and select the shading method.
Cruise Tools offers three multiplication based shading modes:  
  - **Hillshade** is shaded with a synthetic light source, 315° Azimuth, 45° Altitude
  - **Slope** is shaded with the stretched slope inclination
  - **Combo shaded** is a combination of the two, bringing together the best aspects of both methods. Also widely known as *Simon's magical relief visualization*

Note: The created raster will be loaded into the canvas. Please don't freak out
if you have holes in the grid. The reason might be your selection of color bar
and the fact that QGIS reads any RGB value that contains a 0 on any band as
`NoData`. However, your file itself is fine.
___

### Calculate Raster Coverage
This little tool lets you calculate the coverage of a loaded raster band. It will first calculate the entire covered area of the square grid. If a `NoData` value is set, it will additionally give you the actual data coverage in the grid (calculated by percentage of `NoData` values).  
Coverages are calculated based on the project's CRS ellipsoid.

## Contour
### Create Contours
You just used the Load Bathymetry function to show your beautiful seafloor topography. But now you want contour lines to make it a bit more readable.  
Creating contours in QGIS is usually a quicky, however, that’s where the work begins. You might want to have smoothed contours, you might want to filter the little short bits out, and you might want to add some contour labels that are pointing in the cartographically correct direction (up hill). Simply select the bathymetry raster layer and click the button, select your interval and Cruise Tools will create the smoothed contours and apply the style you might have been looking for.  
Contours are filtered by length by a SQL subset filter that is easily adjusted (only when using the toolbar icon, not the toolbox algortihm).

## Vector
### Write Point Coordinates
You just created your point feature layer with all your selected stations but now you need the coordinates, not only in decimal degrees (DD) but also in degrees decimal minutes (DDM) and maybe even the XY coordinates of an entirely separate projection. Use Cruise Tools to fill the layer’s attribute table with all the coordinates you need. **\***
___

### Write Line Length
You just planned your survey lines with a line feature layer and now you need to figure out how long those are in nautical miles or kilometers or meters to get a time estimate for the survey. Yet, using a measurement tool for that is tedious. Use Cruise Tools to fill the layer’s attribute table with all the distance measurements you need. **\***  
If a `speed_kn` field exists and is filled, the steaming time in hours will be written to the `time_h` field, if that exists as well.
___

### Write Polygon Area
You just selected an area of interest (or multiple) for your cruise and now you need an idea of the area size in square meters or square kilometers. Use Cruise Tools to do those measurements and fill the attribute table of your layer. **\***  
**\*** All measurements are ellipsoidal based on the project's CRS ellipsoid. Latitude/Longitude coordinates refer to `WGS84 (EPSG:4326)`.
___

### Swap Vectors
This is a helper tool for contour lines since bathymetry/topography grids sometimes come positive up and sometimes positive down. Depending on this the contour line vectors might have the wrong direction and need to be swapped in order to set the labels right. Use Cruise Tools to flip those vector directions around like it’s nothing.

## Planning
### General Info
The entire Planning menu is intended to create a base for easy export from QGIS into various (vessel specific) exchange formats for the bridge's ECDIS. It has a big fat `under construction` sign on it, but is, for a limited number of vessels, already usable. The idea is that the user creates a point or line planning file from within Cruise Tools, which will a) have a number of fields set up that are useful for the output formats and b) have a style applied that might be handy. Then the layer can be filled with features and the table filled with attributes. When exporting to bridge, Cruise Tools will deal with your geometry type, add point coordinates and handle the output format. So far only RV Sonne and RV Maria S. Merian have output formats that are specific to a certain ECDIS import mechanism. In both cases that is the *SAM Route to Bridge* tool and the exported `CSV` needs to be copied into one of the empty SAM Route `XLSX` sheets. For other ships this is for now just a default `CSV` export which simply contains all attributes and the geometry of the features.  
Additionally, since v1.1, there is a MBES coverage planning tool. See below.
___

### Create Planning File
Create a point / line layer for station planning.
___

### Planning Lines to Vertices
Convert a line layer to a point feature layer with vertices. If a selection in the line layer exists, only selected features will be converted.
___

### Calculate MBES Coverage
Planned your survey over a coarse resolution bathymetry grid like `GEBCO` and need to check if the coverage of your lawn mower pattern create sufficient overlap? This tool lets you combine line planning and bathymetry base in order to get an approximated MBES coverage at specific swath angle settings (depth dependet buffer) to visualize your potential survey coverage results.  
Your segments (from vertex to vertex) will be projected in `Mercator (EPSG:3395)` cartesian lines and the buffer distance is calculated in an apropriate `UTM projection`.  
All independent of your layer and project CRS.
___

### Export to Bridge
Export a planning layer to your vessel specific exchange format. The export tool works with both point and line layers. Line layers will be converted to vertices temporarily. If a selection in the planning layer exists, only selected features will be exported.

## Issues
If you have any issues with the plugin, we are on GitHub:  
https://github.com/simondreutter/cruisetools  
But feel free to contact us via email if you have any comments or wishes or suggestions for improvement, and we’ll see what we can do!s
