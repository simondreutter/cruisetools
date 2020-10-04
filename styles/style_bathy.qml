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
    <rasterrenderer classificationMin="-5000" opacity="1" alphaBand="-1" type="singlebandpseudocolor" classificationMax="0" band="1">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader clip="0" colorRampType="INTERPOLATED" classificationMode="1">
          <colorramp name="[source]" type="cpt-city">
            <prop v="0" k="inverted"/>
            <prop v="cpt-city" k="rampType"/>
            <prop v="grass/haxby" k="schemeName"/>
            <prop v="" k="variantName"/>
          </colorramp>
          <item value="-5000" color="#2539af" alpha="255" label="-5000"/>
          <item value="-4500" color="#287ffb" alpha="255" label="-4500"/>
          <item value="-4000" color="#32beff" alpha="255" label="-4000"/>
          <item value="-3500" color="#6aebff" alpha="255" label="-3500"/>
          <item value="-3000" color="#8aecae" alpha="255" label="-3000"/>
          <item value="-2500" color="#cdffa2" alpha="255" label="-2500"/>
          <item value="-2000" color="#f0ec79" alpha="255" label="-2000"/>
          <item value="-1500" color="#ffbd57" alpha="255" label="-1500"/>
          <item value="-1000" color="#ffa144" alpha="255" label="-1000"/>
          <item value="-500" color="#ffba85" alpha="255" label="-500"/>
          <item value="0" color="#ffffff" alpha="255" label="0"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast contrast="10" brightness="-20"/>
    <huesaturation saturation="0" colorizeGreen="128" colorizeOn="0" colorizeRed="255" colorizeBlue="128" colorizeStrength="100" grayscaleMode="0"/>
    <rasterresampler zoomedInResampler="bilinear" maxOversampling="2" zoomedOutResampler="bilinear"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
