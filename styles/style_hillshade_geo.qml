<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis hasScaleBasedVisibilityFlag="0" minScale="1e+08" maxScale="0" version="3.8.0-Zanzibar" styleCategories="AllStyleCategories">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>0</Searchable>
  </flags>
  <customproperties>
    <property key="WMSBackgroundLayer" value="false"/>
    <property key="WMSPublishDataSourceUrl" value="false"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="identify/format" value="Value"/>
  </customproperties>
  <pipe>
    <rasterrenderer type="hillshade" alphaBand="-1" zfactor="4e-05" azimuth="315" band="1" opacity="0.5" angle="45" multidirection="0">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
    </rasterrenderer>
    <brightnesscontrast contrast="0" brightness="20"/>
    <huesaturation colorizeBlue="128" colorizeRed="255" colorizeGreen="128" grayscaleMode="0" colorizeOn="0" saturation="10" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2" zoomedInResampler="bilinear" zoomedOutResampler="bilinear"/>
  </pipe>
  <blendMode>6</blendMode>
</qgis>
