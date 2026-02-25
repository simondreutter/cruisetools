<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology|Labeling" version="3.38.0-Grenoble">
  <pipe-data-defined-properties>
    <Option type="Map">
      <Option value="" type="QString" name="name"/>
      <Option name="properties"/>
      <Option value="collection" type="QString" name="type"/>
    </Option>
  </pipe-data-defined-properties>
  <pipe>
    <provider>
      <resampling zoomedOutResamplingMethod="nearestNeighbour" zoomedInResamplingMethod="nearestNeighbour" enabled="false" maxOversampling="2"/>
    </provider>
    <rasterrenderer classificationMin="-12000" band="1" opacity="1" alphaBand="-1" nodataColor="" classificationMax="30000" type="singlebandpseudocolor">
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
        <colorrampshader maximumValue="30000" clip="0" minimumValue="-12000" colorRampType="INTERPOLATED" labelPrecision="0" classificationMode="1">
          <colorramp type="gradient" name="[source]">
            <Option type="Map">
              <Option value="40,53,64,255,rgb:0.15686274509803921,0.20784313725490197,0.25098039215686274,1" type="QString" name="color1"/>
              <Option value="255,255,255,255,rgb:1,1,1,1" type="QString" name="color2"/>
              <Option value="ccw" type="QString" name="direction"/>
              <Option value="0" type="QString" name="discrete"/>
              <Option value="gradient" type="QString" name="rampType"/>
              <Option value="rgb" type="QString" name="spec"/>
              <Option value="0.142857;68,92,110,255,rgb:0.26666666666666666,0.36078431372549019,0.43137254901960786,1;rgb;ccw:0.261905;142,209,229,255,rgb:0.55686274509803924,0.81960784313725488,0.89803921568627454,1;rgb;ccw:0.285476;232,250,255,255,rgb:0.90980392156862744,0.98039215686274506,1,1;rgb;ccw:0.285714;255,255,255,255,rgb:1,1,1,1;rgb;ccw:0.285952;230,230,230,255,rgb:0.90196078431372551,0.90196078431372551,0.90196078431372551,1;rgb;ccw:0.288095;204,204,204,255,rgb:0.80000000000000004,0.80000000000000004,0.80000000000000004,1;rgb;ccw:0.309524;179,179,179,255,rgb:0.70196078431372544,0.70196078431372544,0.70196078431372544,1;rgb;ccw:0.52381;153,153,153,255,rgb:0.59999999999999998,0.59999999999999998,0.59999999999999998,1;rgb;ccw:0.761905;250,250,250,255,rgb:0.98039215686274506,0.98039215686274506,0.98039215686274506,1;rgb;ccw" type="QString" name="stops"/>
            </Option>
          </colorramp>
          <item color="#283540" label="-12000" alpha="255" value="-12000"/>
          <item color="#445c6e" label="-6000" alpha="255" value="-6000"/>
          <item color="#8ed1e5" label="-1000" alpha="255" value="-1000"/>
          <item color="#e8faff" label="-10" alpha="255" value="-10"/>
          <item color="#ffffff" label="0" alpha="255" value="0"/>
          <item color="#e6e6e6" label="10" alpha="255" value="10"/>
          <item color="#cccccc" label="100" alpha="255" value="100"/>
          <item color="#b3b3b3" label="1000" alpha="255" value="1000"/>
          <item color="#999999" label="10000" alpha="255" value="10000"/>
          <item color="#fafafa" label="Shelf Ice" alpha="255" value="20000"/>
          <item color="#ffffff" label="Ice Sheet" alpha="255" value="30000"/>
          <rampLegendSettings minimumLabel="" direction="0" maximumLabel="" useContinuousLegend="1" prefix="" suffix="" orientation="2">
            <numericFormat id="basic">
              <Option type="Map">
                <Option type="invalid" name="decimal_separator"/>
                <Option value="6" type="int" name="decimals"/>
                <Option value="0" type="int" name="rounding_type"/>
                <Option value="false" type="bool" name="show_plus"/>
                <Option value="true" type="bool" name="show_thousand_separator"/>
                <Option value="false" type="bool" name="show_trailing_zeros"/>
                <Option type="invalid" name="thousand_separator"/>
              </Option>
            </numericFormat>
          </rampLegendSettings>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast gamma="1" brightness="0" contrast="0"/>
    <huesaturation grayscaleMode="0" colorizeBlue="128" colorizeStrength="100" invertColors="0" colorizeGreen="128" saturation="0" colorizeRed="255" colorizeOn="0"/>
    <rasterresampler maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
