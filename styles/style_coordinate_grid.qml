<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology|Labeling" labelsEnabled="1" version="3.34.0-Prizren">
  <renderer-v2 forceraster="0" referencescale="-1" symbollevels="0" type="RuleRenderer" enableorderby="0">
    <rules key="{a151ab6b-85d6-4d98-85bc-388acf620c22}">
      <rule key="{130766ad-9f68-4dda-857f-0fd6327c9a84}" scalemindenom="100000000" label="deg % 40" scalemaxdenom="1000000000" filter="-- IF CRS is polar stereographic:&#xa;if(@map_crs_acronym='stere',&#xa;(&quot;latlon&quot; = 'lon' AND deg % 40 = 0) OR &#xa;(&quot;latlon&quot; = 'lat' AND deg % 20 = 0) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = maximum(deg,&quot;latlon&quot; = 'lat')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = minimum(deg,&quot;latlon&quot; = 'lat')) OR&#xa;(&quot;latlon&quot; = 'lon' AND deg = maximum(deg,&quot;latlon&quot; = 'lon')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = minimum(deg,&quot;latlon&quot; = 'lon'))&#xd;&#xa;= 1,&#xa;-- ELSE:&#xa;(&quot;latlon&quot; = 'lon' AND deg % 40 = 0) OR &#xa;(&quot;latlon&quot; = 'lat' AND deg % 40 = 0) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = maximum(deg,&quot;latlon&quot; = 'lat')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = minimum(deg,&quot;latlon&quot; = 'lat')) OR&#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = maximum(deg,&quot;latlon&quot; = 'lon')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = minimum(deg,&quot;latlon&quot; = 'lon'))&#xa;=1)" symbol="0"/>
      <rule key="{39f0c109-4e52-41f6-b74e-97b223c87ac8}" scalemindenom="50000000" label="deg % 20" scalemaxdenom="100000000" filter="-- IF CRS is polar stereographic:&#xd;&#xa;if(@map_crs_acronym='stere',&#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg % 20 = 0) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg % 10 = 0) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = maximum(deg,&quot;latlon&quot; = 'lat')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = minimum(deg,&quot;latlon&quot; = 'lat')) OR&#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = maximum(deg,&quot;latlon&quot; = 'lon')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = minimum(deg,&quot;latlon&quot; = 'lon'))&#xd;&#xa;= 1,&#xd;&#xa;-- ELSE:&#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg % 20 = 0) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg % 20 = 0) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = maximum(deg,&quot;latlon&quot; = 'lat')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = minimum(deg,&quot;latlon&quot; = 'lat')) OR&#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = maximum(deg,&quot;latlon&quot; = 'lon')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = minimum(deg,&quot;latlon&quot; = 'lon'))&#xd;&#xa;=1)" symbol="1"/>
      <rule key="{39f0c109-4e52-41f6-b74e-97b223c87ac8}" scalemindenom="10000001" label="deg % 10" scalemaxdenom="50000000" filter="-- IF CRS is polar stereographic:&#xa;if(@map_crs_acronym='stere',&#xa;(&quot;latlon&quot; = 'lon' AND deg % 10 = 0) OR &#xa;(&quot;latlon&quot; = 'lat' AND deg % 5 = 0) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = maximum(deg,&quot;latlon&quot; = 'lat')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = minimum(deg,&quot;latlon&quot; = 'lat')) OR&#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = maximum(deg,&quot;latlon&quot; = 'lon')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = minimum(deg,&quot;latlon&quot; = 'lon'))&#xa;= 1,&#xa;-- ELSE:&#xa;(&quot;latlon&quot; = 'lon' AND deg % 10 = 0) OR &#xa;(&quot;latlon&quot; = 'lat' AND deg % 10 = 0) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = maximum(deg,&quot;latlon&quot; = 'lat')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = minimum(deg,&quot;latlon&quot; = 'lat')) OR&#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = maximum(deg,&quot;latlon&quot; = 'lon')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = minimum(deg,&quot;latlon&quot; = 'lon'))&#xa;=1)" symbol="2"/>
      <rule key="{86feba18-a4ac-409b-a795-ebd76dfd1e2b}" scalemindenom="5000001" label="deg % 5" scalemaxdenom="10000000" filter="-- IF CRS is polar stereographic:&#xa;if(@map_crs_acronym='stere',&#xa;(&quot;latlon&quot; = 'lon' AND deg % 5 = 0) OR &#xa;(&quot;latlon&quot; = 'lat' AND deg % 2 = 0) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = maximum(deg,&quot;latlon&quot; = 'lat')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = minimum(deg,&quot;latlon&quot; = 'lat')) OR&#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = maximum(deg,&quot;latlon&quot; = 'lon')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = minimum(deg,&quot;latlon&quot; = 'lon'))&#xa;= 1,&#xa;-- ELSE:&#xa;(&quot;latlon&quot; = 'lon' AND deg % 5 = 0) OR &#xa;(&quot;latlon&quot; = 'lat' AND deg % 5 = 0) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = maximum(deg,&quot;latlon&quot; = 'lat')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = minimum(deg,&quot;latlon&quot; = 'lat')) OR&#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = maximum(deg,&quot;latlon&quot; = 'lon')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = minimum(deg,&quot;latlon&quot; = 'lon'))&#xa;=1)" symbol="3"/>
      <rule key="{df9fcbae-4bef-48dc-998b-6d0d94065828}" scalemindenom="2500001" label="deg % 2" scalemaxdenom="5000000" filter="-- IF CRS is polar stereographic:&#xa;if(@map_crs_acronym='stere',&#xa;(&quot;latlon&quot; = 'lon' AND deg % 2 = 0) OR &#xa;(&quot;latlon&quot; = 'lat' AND deg % 1 = 0) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = maximum(deg,&quot;latlon&quot; = 'lat')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = minimum(deg,&quot;latlon&quot; = 'lat')) OR&#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = maximum(deg,&quot;latlon&quot; = 'lon')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = minimum(deg,&quot;latlon&quot; = 'lon'))&#xa;= 1,&#xa;-- ELSE:&#xa;(&quot;latlon&quot; = 'lon' AND deg % 2 = 0) OR &#xa;(&quot;latlon&quot; = 'lat' AND deg % 2 = 0) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = maximum(deg,&quot;latlon&quot; = 'lat')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = minimum(deg,&quot;latlon&quot; = 'lat')) OR&#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = maximum(deg,&quot;latlon&quot; = 'lon')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = minimum(deg,&quot;latlon&quot; = 'lon'))&#xa;=1)" symbol="4"/>
      <rule key="{6281c7d4-414f-4c82-a83c-b5711eb6d4c0}" scalemindenom="1000001" label="deg % 1" scalemaxdenom="2500000" filter="-- IF CRS is polar stereographic:&#xa;if(@map_crs_acronym='stere',&#xa;(&quot;latlon&quot; = 'lon' AND deg % 1 = 0) OR &#xa;(&quot;latlon&quot; = 'lat' AND deg % 0.5 = 0) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = maximum(deg,&quot;latlon&quot; = 'lat')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = minimum(deg,&quot;latlon&quot; = 'lat')) OR&#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = maximum(deg,&quot;latlon&quot; = 'lon')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = minimum(deg,&quot;latlon&quot; = 'lon'))&#xa;= 1,&#xa;-- ELSE:&#xa;(&quot;latlon&quot; = 'lon' AND deg % 1 = 0) OR &#xa;(&quot;latlon&quot; = 'lat' AND deg % 1 = 0) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = maximum(deg,&quot;latlon&quot; = 'lat')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = minimum(deg,&quot;latlon&quot; = 'lat')) OR&#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = maximum(deg,&quot;latlon&quot; = 'lon')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = minimum(deg,&quot;latlon&quot; = 'lon'))&#xa;=1)" symbol="5"/>
      <rule key="{d8d37f61-3236-4ef4-b4c2-9215889f8abc}" scalemindenom="500001" label="deg % 0.5" scalemaxdenom="1000000" filter="-- IF CRS is polar stereographic:&#xa;if(@map_crs_acronym='stere',&#xa;(&quot;latlon&quot; = 'lon' AND deg % 0.5 = 0) OR &#xa;(&quot;latlon&quot; = 'lat' AND deg % 0.25 = 0) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = maximum(deg,&quot;latlon&quot; = 'lat')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = minimum(deg,&quot;latlon&quot; = 'lat')) OR&#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = maximum(deg,&quot;latlon&quot; = 'lon')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = minimum(deg,&quot;latlon&quot; = 'lon'))&#xa;= 1,&#xa;-- ELSE:&#xa;(&quot;latlon&quot; = 'lon' AND deg % 0.5 = 0) OR &#xa;(&quot;latlon&quot; = 'lat' AND deg % 0.5 = 0) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = maximum(deg,&quot;latlon&quot; = 'lat')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lat' AND deg = minimum(deg,&quot;latlon&quot; = 'lat')) OR&#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = maximum(deg,&quot;latlon&quot; = 'lon')) OR &#xd;&#xa;(&quot;latlon&quot; = 'lon' AND deg = minimum(deg,&quot;latlon&quot; = 'lon'))&#xa;=1)" symbol="6"/>
      <rule key="{c8ff4438-7c29-43f9-ae33-8f6d2be233a5}" scalemindenom="1" label="all" scalemaxdenom="500000" filter="TRUE" symbol="7"/>
    </rules>
    <symbols>
      <symbol is_animated="0" frame_rate="10" force_rhr="0" clip_to_extent="1" type="line" name="0" alpha="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" class="SimpleLine" locked="0" id="{623a2c9b-b030-454c-b4ba-18b0d249c619}" pass="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="227,26,28,255" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.2" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol is_animated="0" frame_rate="10" force_rhr="0" clip_to_extent="1" type="line" name="1" alpha="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" class="SimpleLine" locked="0" id="{e31a9b6b-68de-433c-a3e9-a1ea1e257014}" pass="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="227,26,28,255" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.2" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol is_animated="0" frame_rate="10" force_rhr="0" clip_to_extent="1" type="line" name="2" alpha="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" class="SimpleLine" locked="0" id="{b36732f7-6f5f-4ff0-953d-7f873c25404c}" pass="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="227,26,28,255" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.2" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol is_animated="0" frame_rate="10" force_rhr="0" clip_to_extent="1" type="line" name="3" alpha="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" class="SimpleLine" locked="0" id="{efb488d0-5f93-48e5-a856-3c965ec83b7f}" pass="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="227,26,28,255" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.2" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol is_animated="0" frame_rate="10" force_rhr="0" clip_to_extent="1" type="line" name="4" alpha="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" class="SimpleLine" locked="0" id="{458ef232-f5b2-4bdc-950a-6ed1380bdb0e}" pass="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="227,26,28,255" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.2" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol is_animated="0" frame_rate="10" force_rhr="0" clip_to_extent="1" type="line" name="5" alpha="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" class="SimpleLine" locked="0" id="{458ef232-f5b2-4bdc-950a-6ed1380bdb0e}" pass="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="227,26,28,255" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.2" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol is_animated="0" frame_rate="10" force_rhr="0" clip_to_extent="1" type="line" name="6" alpha="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" class="SimpleLine" locked="0" id="{458ef232-f5b2-4bdc-950a-6ed1380bdb0e}" pass="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="227,26,28,255" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.2" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol is_animated="0" frame_rate="10" force_rhr="0" clip_to_extent="1" type="line" name="7" alpha="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" class="SimpleLine" locked="0" id="{458ef232-f5b2-4bdc-950a-6ed1380bdb0e}" pass="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="227,26,28,255" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.2" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <selection mode="Default">
    <selectionColor invalid="1"/>
    <selectionSymbol>
      <symbol is_animated="0" frame_rate="10" force_rhr="0" clip_to_extent="1" type="line" name="" alpha="1">
        <data_defined_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </data_defined_properties>
        <layer enabled="1" class="SimpleLine" locked="0" id="{98ea1ac2-502e-468b-85a0-884266fba936}" pass="0">
          <Option type="Map">
            <Option value="0" type="QString" name="align_dash_pattern"/>
            <Option value="square" type="QString" name="capstyle"/>
            <Option value="5;2" type="QString" name="customdash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="customdash_map_unit_scale"/>
            <Option value="MM" type="QString" name="customdash_unit"/>
            <Option value="0" type="QString" name="dash_pattern_offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="dash_pattern_offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="dash_pattern_offset_unit"/>
            <Option value="0" type="QString" name="draw_inside_polygon"/>
            <Option value="bevel" type="QString" name="joinstyle"/>
            <Option value="35,35,35,255" type="QString" name="line_color"/>
            <Option value="solid" type="QString" name="line_style"/>
            <Option value="0.26" type="QString" name="line_width"/>
            <Option value="MM" type="QString" name="line_width_unit"/>
            <Option value="0" type="QString" name="offset"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
            <Option value="MM" type="QString" name="offset_unit"/>
            <Option value="0" type="QString" name="ring_filter"/>
            <Option value="0" type="QString" name="trim_distance_end"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_end_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_end_unit"/>
            <Option value="0" type="QString" name="trim_distance_start"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="trim_distance_start_map_unit_scale"/>
            <Option value="MM" type="QString" name="trim_distance_start_unit"/>
            <Option value="0" type="QString" name="tweak_dash_pattern_on_corners"/>
            <Option value="0" type="QString" name="use_custom_dash"/>
            <Option value="3x:0,0,0,0,0,0" type="QString" name="width_map_unit_scale"/>
          </Option>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option name="properties"/>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </selectionSymbol>
  </selection>
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style fontUnderline="0" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontWordSpacing="0" fontKerning="1" textColor="255,0,0,255" fontSizeUnit="Point" fontWeight="50" fieldName="label" forcedBold="0" capitalization="0" fontStrikeout="0" multilineHeight="1" multilineHeightUnit="Percentage" useSubstitutions="0" blendMode="0" textOpacity="1" textOrientation="horizontal" previewBkgrdColor="255,255,255,255" allowHtml="0" fontItalic="0" fontLetterSpacing="0" forcedItalic="0" fontSize="8" fontFamily="MS Shell Dlg 2" isExpression="0" namedStyle="Regular" legendString="Aa">
        <families/>
        <text-buffer bufferSizeUnits="MM" bufferOpacity="0.5" bufferNoFill="0" bufferColor="255,255,255,255" bufferBlendMode="0" bufferSize="1" bufferJoinStyle="128" bufferDraw="1" bufferSizeMapUnitScale="3x:0,0,0,0,0,0"/>
        <text-mask maskJoinStyle="128" maskOpacity="1" maskEnabled="0" maskSize="0" maskSizeMapUnitScale="3x:0,0,0,0,0,0" maskType="0" maskSizeUnits="MM" maskedSymbolLayers=""/>
        <background shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetX="0" shapeOffsetUnit="MM" shapeFillColor="255,255,255,255" shapeOffsetY="0" shapeRotation="0" shapeSizeUnit="MM" shapeBorderWidthUnit="MM" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiX="0" shapeSizeType="0" shapeOpacity="1" shapeSizeX="0" shapeBorderColor="128,128,128,255" shapeDraw="0" shapeRotationType="0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeRadiiY="0" shapeSVGFile="" shapeBorderWidth="0" shapeJoinStyle="64" shapeRadiiUnit="MM" shapeSizeY="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeBlendMode="0" shapeType="0">
          <symbol is_animated="0" frame_rate="10" force_rhr="0" clip_to_extent="1" type="marker" name="markerSymbol" alpha="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" class="SimpleMarker" locked="0" id="" pass="0">
              <Option type="Map">
                <Option value="0" type="QString" name="angle"/>
                <Option value="square" type="QString" name="cap_style"/>
                <Option value="152,125,183,255" type="QString" name="color"/>
                <Option value="1" type="QString" name="horizontal_anchor_point"/>
                <Option value="bevel" type="QString" name="joinstyle"/>
                <Option value="circle" type="QString" name="name"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="35,35,35,255" type="QString" name="outline_color"/>
                <Option value="solid" type="QString" name="outline_style"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="outline_width_map_unit_scale"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option value="diameter" type="QString" name="scale_method"/>
                <Option value="2" type="QString" name="size"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="size_map_unit_scale"/>
                <Option value="MM" type="QString" name="size_unit"/>
                <Option value="1" type="QString" name="vertical_anchor_point"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
          <symbol is_animated="0" frame_rate="10" force_rhr="0" clip_to_extent="1" type="fill" name="fillSymbol" alpha="1">
            <data_defined_properties>
              <Option type="Map">
                <Option value="" type="QString" name="name"/>
                <Option name="properties"/>
                <Option value="collection" type="QString" name="type"/>
              </Option>
            </data_defined_properties>
            <layer enabled="1" class="SimpleFill" locked="0" id="" pass="0">
              <Option type="Map">
                <Option value="3x:0,0,0,0,0,0" type="QString" name="border_width_map_unit_scale"/>
                <Option value="255,255,255,255" type="QString" name="color"/>
                <Option value="bevel" type="QString" name="joinstyle"/>
                <Option value="0,0" type="QString" name="offset"/>
                <Option value="3x:0,0,0,0,0,0" type="QString" name="offset_map_unit_scale"/>
                <Option value="MM" type="QString" name="offset_unit"/>
                <Option value="128,128,128,255" type="QString" name="outline_color"/>
                <Option value="no" type="QString" name="outline_style"/>
                <Option value="0" type="QString" name="outline_width"/>
                <Option value="MM" type="QString" name="outline_width_unit"/>
                <Option value="solid" type="QString" name="style"/>
              </Option>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" type="QString" name="name"/>
                  <Option name="properties"/>
                  <Option value="collection" type="QString" name="type"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </background>
        <shadow shadowOffsetUnit="MM" shadowRadiusUnit="MM" shadowBlendMode="6" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowOffsetAngle="135" shadowRadiusAlphaOnly="0" shadowOpacity="0.69999999999999996" shadowDraw="0" shadowRadius="1.5" shadowScale="100" shadowOffsetGlobal="1" shadowColor="0,0,0,255" shadowUnder="0" shadowOffsetDist="1"/>
        <dd_properties>
          <Option type="Map">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format useMaxLineLengthForAutoWrap="1" leftDirectionSymbol="&lt;" reverseDirectionSymbol="0" plussign="0" placeDirectionSymbol="0" autoWrapLength="0" addDirectionSymbol="0" decimals="3" multilineAlign="0" wrapChar="" rightDirectionSymbol=">" formatNumbers="0"/>
      <placement repeatDistanceUnits="MM" overlapHandling="PreventOverlap" quadOffset="4" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" maxCurvedCharAngleIn="25" distMapUnitScale="3x:0,0,0,0,0,0" priority="5" geometryGenerator="" lineAnchorClipping="0" fitInPolygonOnly="0" preserveRotation="1" allowDegraded="0" xOffset="0" overrunDistance="0" overrunDistanceUnit="MM" lineAnchorType="0" offsetUnits="MapUnit" lineAnchorTextPoint="CenterOfText" yOffset="0" distUnits="MM" offsetType="0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" rotationUnit="AngleDegrees" lineAnchorPercent="0.5" repeatDistance="0" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" placement="2" centroidInside="0" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" placementFlags="9" dist="0" centroidWhole="0" polygonPlacementFlags="2" layerType="LineGeometry" maxCurvedCharAngleOut="-25" geometryGeneratorEnabled="0" rotationAngle="0" geometryGeneratorType="PointGeometry"/>
      <rendering unplacedVisibility="0" drawLabels="1" mergeLines="0" zIndex="0" fontLimitPixelSize="0" obstacleType="0" scaleVisibility="0" minFeatureSize="0" obstacle="1" maxNumLabels="2000" labelPerPart="0" scaleMax="10000000" fontMaxPixelSize="10000" limitNumLabels="0" fontMinPixelSize="3" scaleMin="1" upsidedownLabels="0" obstacleFactor="1"/>
      <dd_properties>
        <Option type="Map">
          <Option value="" type="QString" name="name"/>
          <Option name="properties"/>
          <Option value="collection" type="QString" name="type"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option value="pole_of_inaccessibility" type="QString" name="anchorPoint"/>
          <Option value="0" type="int" name="blendMode"/>
          <Option type="Map" name="ddProperties">
            <Option value="" type="QString" name="name"/>
            <Option name="properties"/>
            <Option value="collection" type="QString" name="type"/>
          </Option>
          <Option value="false" type="bool" name="drawToAllParts"/>
          <Option value="0" type="QString" name="enabled"/>
          <Option value="point_on_exterior" type="QString" name="labelAnchorPoint"/>
          <Option value="&lt;symbol is_animated=&quot;0&quot; frame_rate=&quot;10&quot; force_rhr=&quot;0&quot; clip_to_extent=&quot;1&quot; type=&quot;line&quot; name=&quot;symbol&quot; alpha=&quot;1&quot;>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option value=&quot;&quot; type=&quot;QString&quot; name=&quot;name&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option value=&quot;collection&quot; type=&quot;QString&quot; name=&quot;type&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;layer enabled=&quot;1&quot; class=&quot;SimpleLine&quot; locked=&quot;0&quot; id=&quot;{32c2942c-e27a-40f2-abc4-84ca8cec322b}&quot; pass=&quot;0&quot;>&lt;Option type=&quot;Map&quot;>&lt;Option value=&quot;0&quot; type=&quot;QString&quot; name=&quot;align_dash_pattern&quot;/>&lt;Option value=&quot;square&quot; type=&quot;QString&quot; name=&quot;capstyle&quot;/>&lt;Option value=&quot;5;2&quot; type=&quot;QString&quot; name=&quot;customdash&quot;/>&lt;Option value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot; name=&quot;customdash_map_unit_scale&quot;/>&lt;Option value=&quot;MM&quot; type=&quot;QString&quot; name=&quot;customdash_unit&quot;/>&lt;Option value=&quot;0&quot; type=&quot;QString&quot; name=&quot;dash_pattern_offset&quot;/>&lt;Option value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot; name=&quot;dash_pattern_offset_map_unit_scale&quot;/>&lt;Option value=&quot;MM&quot; type=&quot;QString&quot; name=&quot;dash_pattern_offset_unit&quot;/>&lt;Option value=&quot;0&quot; type=&quot;QString&quot; name=&quot;draw_inside_polygon&quot;/>&lt;Option value=&quot;bevel&quot; type=&quot;QString&quot; name=&quot;joinstyle&quot;/>&lt;Option value=&quot;60,60,60,255&quot; type=&quot;QString&quot; name=&quot;line_color&quot;/>&lt;Option value=&quot;solid&quot; type=&quot;QString&quot; name=&quot;line_style&quot;/>&lt;Option value=&quot;0.3&quot; type=&quot;QString&quot; name=&quot;line_width&quot;/>&lt;Option value=&quot;MM&quot; type=&quot;QString&quot; name=&quot;line_width_unit&quot;/>&lt;Option value=&quot;0&quot; type=&quot;QString&quot; name=&quot;offset&quot;/>&lt;Option value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot; name=&quot;offset_map_unit_scale&quot;/>&lt;Option value=&quot;MM&quot; type=&quot;QString&quot; name=&quot;offset_unit&quot;/>&lt;Option value=&quot;0&quot; type=&quot;QString&quot; name=&quot;ring_filter&quot;/>&lt;Option value=&quot;0&quot; type=&quot;QString&quot; name=&quot;trim_distance_end&quot;/>&lt;Option value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot; name=&quot;trim_distance_end_map_unit_scale&quot;/>&lt;Option value=&quot;MM&quot; type=&quot;QString&quot; name=&quot;trim_distance_end_unit&quot;/>&lt;Option value=&quot;0&quot; type=&quot;QString&quot; name=&quot;trim_distance_start&quot;/>&lt;Option value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot; name=&quot;trim_distance_start_map_unit_scale&quot;/>&lt;Option value=&quot;MM&quot; type=&quot;QString&quot; name=&quot;trim_distance_start_unit&quot;/>&lt;Option value=&quot;0&quot; type=&quot;QString&quot; name=&quot;tweak_dash_pattern_on_corners&quot;/>&lt;Option value=&quot;0&quot; type=&quot;QString&quot; name=&quot;use_custom_dash&quot;/>&lt;Option value=&quot;3x:0,0,0,0,0,0&quot; type=&quot;QString&quot; name=&quot;width_map_unit_scale&quot;/>&lt;/Option>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option value=&quot;&quot; type=&quot;QString&quot; name=&quot;name&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option value=&quot;collection&quot; type=&quot;QString&quot; name=&quot;type&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>" type="QString" name="lineSymbol"/>
          <Option value="0" type="double" name="minLength"/>
          <Option value="3x:0,0,0,0,0,0" type="QString" name="minLengthMapUnitScale"/>
          <Option value="MM" type="QString" name="minLengthUnit"/>
          <Option value="0" type="double" name="offsetFromAnchor"/>
          <Option value="3x:0,0,0,0,0,0" type="QString" name="offsetFromAnchorMapUnitScale"/>
          <Option value="MM" type="QString" name="offsetFromAnchorUnit"/>
          <Option value="0" type="double" name="offsetFromLabel"/>
          <Option value="3x:0,0,0,0,0,0" type="QString" name="offsetFromLabelMapUnitScale"/>
          <Option value="MM" type="QString" name="offsetFromLabelUnit"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerGeometryType>1</layerGeometryType>
</qgis>
