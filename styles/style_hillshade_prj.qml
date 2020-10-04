<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.8.0-Zanzibar" minScale="1e+08" maxScale="0" hasScaleBasedVisibilityFlag="0" styleCategories="AllStyleCategories">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <customproperties>
    <property key="WMSBackgroundLayer" value="false"/>
    <property key="WMSPublishDataSourceUrl" value="false"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="identify/format" value="Value"/>
  </customproperties>
  <pipe>
    <rasterrenderer multidirection="0" zfactor="5" opacity="0.5" alphaBand="-1" angle="45" azimuth="315" type="hillshade" band="1">
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
    <huesaturation saturation="10" colorizeGreen="128" colorizeOn="0" colorizeRed="255" colorizeBlue="128" colorizeStrength="100" grayscaleMode="0"/>
    <rasterresampler zoomedInResampler="bilinear" maxOversampling="2" zoomedOutResampler="bilinear"/>
  </pipe>
  <blendMode>6</blendMode>
</qgis>
