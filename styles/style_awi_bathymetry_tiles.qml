<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.34.0-Prizren" styleCategories="Symbology|Labeling">
  <pipe-data-defined-properties>
    <Option type="Map">
      <Option type="QString" name="name" value=""/>
      <Option name="properties"/>
      <Option type="QString" name="type" value="collection"/>
    </Option>
  </pipe-data-defined-properties>
  <pipe>
    <provider>
      <resampling zoomedOutResamplingMethod="nearestNeighbour" zoomedInResamplingMethod="nearestNeighbour" maxOversampling="2" enabled="false"/>
    </provider>
    <rasterrenderer band="1" type="singlebandpseudocolor" classificationMin="-12000" nodataColor="" opacity="1" classificationMax="0" alphaBand="-1">
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
        <colorrampshader classificationMode="1" clip="0" labelPrecision="4" minimumValue="-12000" maximumValue="0" colorRampType="INTERPOLATED">
          <colorramp type="gradient" name="[source]">
            <Option type="Map">
              <Option type="QString" name="color1" value="27,42,128,255"/>
              <Option type="QString" name="color2" value="255,0,0,255"/>
              <Option type="QString" name="direction" value="ccw"/>
              <Option type="QString" name="discrete" value="0"/>
              <Option type="QString" name="rampType" value="gradient"/>
              <Option type="QString" name="spec" value="rgb"/>
              <Option type="QString" name="stops" value="0.5;37,57,175,255;rgb;ccw:0.7;40,127,251,255;rgb;ccw:0.8;50,190,255,255;rgb;ccw:0.86;106,235,255,255;rgb;ccw:0.9;138,236,174,255;rgb;ccw:0.928333;205,255,162,255;rgb;ccw:0.95;240,236,121,255;rgb;ccw:0.966667;255,189,87,255;rgb;ccw:0.98;255,161,68,255;rgb;ccw:0.9875;255,186,133,255;rgb;ccw:0.991667;255,255,255,255;rgb;ccw:0.993333;255,0,0,255;rgb;ccw"/>
            </Option>
          </colorramp>
          <item color="#1b2a80" alpha="255" label="-12000" value="-12000"/>
          <item color="#2539af" alpha="255" label="-6000" value="-6000"/>
          <item color="#287ffb" alpha="255" label="-3600" value="-3600"/>
          <item color="#32beff" alpha="255" label="-2400" value="-2400"/>
          <item color="#6aebff" alpha="255" label="-1680" value="-1680"/>
          <item color="#8aecae" alpha="255" label="-1200" value="-1200"/>
          <item color="#cdffa2" alpha="255" label="-860" value="-860"/>
          <item color="#f0ec79" alpha="255" label="-600" value="-600"/>
          <item color="#ffbd57" alpha="255" label="-400" value="-400"/>
          <item color="#ffa144" alpha="255" label="-240" value="-240"/>
          <item color="#ffba85" alpha="255" label="-150" value="-150"/>
          <item color="#ffffff" alpha="255" label="-100" value="-100"/>
          <item color="#ff0000" alpha="255" label="-80" value="-80"/>
          <item color="#ff0000" alpha="255" label="0" value="0"/>
          <rampLegendSettings useContinuousLegend="1" suffix="" maximumLabel="" direction="0" prefix="" minimumLabel="" orientation="2">
            <numericFormat id="basic">
              <Option type="Map">
                <Option type="invalid" name="decimal_separator"/>
                <Option type="int" name="decimals" value="6"/>
                <Option type="int" name="rounding_type" value="0"/>
                <Option type="bool" name="show_plus" value="false"/>
                <Option type="bool" name="show_thousand_separator" value="true"/>
                <Option type="bool" name="show_trailing_zeros" value="false"/>
                <Option type="invalid" name="thousand_separator"/>
              </Option>
            </numericFormat>
          </rampLegendSettings>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast brightness="0" contrast="0" gamma="1"/>
    <huesaturation colorizeOn="0" saturation="0" grayscaleMode="0" colorizeBlue="128" invertColors="0" colorizeRed="255" colorizeGreen="128" colorizeStrength="100"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
