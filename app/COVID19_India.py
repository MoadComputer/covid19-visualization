import os
import math
import json
import bokeh
import geopandas
import numpy as np
import pandas as pd

from bokeh.io.doc import curdoc
from bokeh.plotting import figure
from bokeh.models.widgets import Button
from bokeh.palettes import brewer, OrRd
from bokeh.plotting import show as plt_show
from bokeh.tile_providers import Vendors, get_provider
from bokeh.io import output_notebook, show, output_file
from bokeh.layouts import widgetbox, row, column, gridplot
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, NumeralTickFormatter
from bokeh.models import Slider, HoverTool, Select, Div, Range1d, WMTSTileSource, BoxZoomTool, TapTool, Panel, Tabs

verbose=False

India_statewise = geopandas.read_file('https://github.com/MoadComputer/covid19-visualization/raw/master/data/GeoJSON_assets/India_statewise_minified.geojson')
India_statewise = India_statewise.to_crs("EPSG:3395")

covid19_data = pd.read_csv('https://github.com/MoadComputer/covid19-visualization/raw/master/data/Coronavirus_stats/India/COVID19_India_statewise.csv')
covid19_data.loc[covid19_data['state'] == 'Telengana', 'state'] = 'Telangana'

noCOVID19_list = list(set(list(India_statewise.state.values)) -set(list(covid19_data.state)))
if verbose:
  print('A total of: {} states with no reports of COVID19 ...'.format(len(noCOVID19_list)))
  print('\nStates in India with no COVID19 reports:')
  for noCOVID19_state in noCOVID19_list:
    print('\n{} ...'.format(noCOVID19_state))

def covid19_json(covid_df, geo_df,verbose=False):
    merged_df = pd.merge(geo_df, covid_df, on='state', how='left')

    try:
      merged_df = merged_df.fillna(0)
    except:
      merged_df.fillna({'total_cases': 0}, inplace=True)
      merged_df.fillna({'deaths': 0}, inplace=True)
      merged_df.fillna({'discharged': 0}, inplace=True)
      if verbose:
        print('Consider updating GeoPandas library ...')
    
    merged_json = json.loads(merged_df.to_json())
    json_data = json.dumps(merged_json)
    return {'json_data': json_data, 'data_frame': merged_df}

merged_data = covid19_json(covid19_data, India_statewise, 
                           verbose=verbose)
merged_json = merged_data['json_data']

def CustomPalette(palette_type):
  if palette_type.lower()=='OrRd'.lower():
    palette = OrRd[9]
    palette = palette[::-1]
  else:
    palette = brewer['Oranges']
    palette = palette[::-1]
  return palette

def CustomHoverTool(enable_advancedStats, custom_hovertool):
  advancedStats_hover=HoverTool(tooltips ="""<strong><font face="Arial" size="2">@state</font></strong> <br>
                                             <font face="Arial" size="2">Cases: @total_cases</font><br>
                                             <font face="Arial" size="2">Deaths: @deaths </font>
                                             <hr>
                                             <strong><font face="Arial" size="2">Cases forecast</font></strong> <br>
                                             <font face="Arial" size="1">+1 day: <strong>@preds_cases</strong></font><br>
                                             <font face="Arial" size="1">+3 days: <strong>@preds_cases_3</strong></font><br>
                                             <font face="Arial" size="1">+7 days: <strong>@preds_cases_7</strong></font><br>
                                             <hr>
                                             <strong><font face="Arial" size="1">Forecast by: https://moad.computer</font></strong> <br>""")

  simpleStats_hover=HoverTool(tooltips ="""<strong><font face="Arial" size="3">@state</font></strong> <br>
                                           <font face="Arial" size="3">Cases: @total_cases</font><br>
                                           <font face="Arial" size="3">Deaths: @deaths </font>""")

  standard_hover = HoverTool(tooltips = [('State','@state'),
                                         ('Cases', '@total_cases'),
                                         #('Discharged/migrated', '@discharged'),
                                         ('Deaths', '@deaths')])
  
  if enable_advancedStats:
    hover = advancedStats_hover
  elif custom_hovertool:
    hover  = simpleStats_hover
  else:
    hover = standard_hover
  return hover

def MapOverlayFormatter(map_overlay):
  if map_overlay:
    xmin = 8450000
    xmax = 10000000
    ymin = 850000
    ymax = 4550000
    
    return xmin, xmax, ymin, ymax

def geographic_overlay(plt, 
                       geosourceJson=None,
                       colorBar=None,
                       colorMapper=None,
                       colorMode='',
                       hoverTool=None,
                       mapOverlay=True,
                       enableTapTool=False,
                       enableToolbar=True):
  if mapOverlay:
    wmts = WMTSTileSource(url="http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png")
    plt.add_tile(wmts)
    plt.xaxis.axis_label = 'longitude'
    plt.yaxis.axis_label = 'latitude'
  
  plt.xgrid.grid_line_color = None
  plt.ygrid.grid_line_color = None
  plt.axis.visible = False
  plt.patches('xs','ys', 
              source = geosourceJson, 
              fill_color = {'field' : colorMode, 
                            'transform' : colorMapper},
              line_color = 'purple', 
              line_width = 0.5, 
              fill_alpha = 0.85)
  plt.add_layout(colorBar, 'right')
  plt.add_tools(hoverTool)
  if enableTapTool:
    plt.add_tools(TapTool())
  if enableToolbar:
    plt.toolbar.autohide = True
  if plt.title is not None:
    plt.title.text_font_size = '30pt'
  return plt

def covid19_plot(covid19_geosource, 
                 input_df=None,
                 input_field=None,
                 plot_title=None,
                 map_overlay=True,
                 palette_type='OrRd',
                 custom_hovertool=True,
                 enable_advancedStats=False,
                 enable_toolbar=False):
  
  palette = CustomPalette(palette_type)
  color_mapper = LinearColorMapper(palette=palette, 
                                   low=0, 
                                   high=int(10*(np.ceil(np.max(input_df[input_field].values)/10))))
  format_tick = NumeralTickFormatter(format=str(input_df[input_field].values.astype('int')))
  color_bar = ColorBar(color_mapper=color_mapper, 
                       label_standoff=11, 
                       formatter=format_tick,
                       border_line_color=None, 
                       major_label_text_font_size='16px',
                       location = (0, 0))
  xmin, xmax, ymin, ymax = MapOverlayFormatter(map_overlay)
  hover = CustomHoverTool(enable_advancedStats, custom_hovertool)

  plt = figure(title = plot_title,
               x_range=(xmin, xmax) if map_overlay else None,
               y_range=(ymin, ymax) if map_overlay else None,
               tools='save' if enable_toolbar else '', 
               plot_height = 600, plot_width = 600,
               toolbar_location = 'left' if enable_toolbar else None,
               lod_factor=int(1e7),
               lod_threshold=int(2),
               output_backend="webgl")
  
  plt = geographic_overlay(plt, 
                           geosourceJson=covid19_geosource,
                           colorBar=color_bar,
                           colorMapper=color_mapper,
                           colorMode=input_field,
                           hoverTool=hover,
                           mapOverlay=map_overlay,
                           enableToolbar=enable_toolbar,
                           enableTapTool=True if enable_advancedStats else False)
  
  return plt

advanced_mode=True
try:
  preds_df=pd.read_csv('https://github.com/MoadComputer/covid19-visualization/raw/master/data/Coronavirus_stats/India/experimental/output_preds.csv')
except:
  print('Advanced mode disabled ...')
  advanced_mode=False

covid19_geosource=GeoJSONDataSource(geojson=merged_json)
plot_title=None#'COVID19 outbreak in India'
app_title='COVID19 India'

basic_covid19_plot = covid19_plot(covid19_geosource, 
                                  input_df=covid19_data,
                                  input_field='deaths',
                                  plot_title=plot_title)
basicPlot_tab = Panel(child=basic_covid19_plot, title=" ■■■ ")

if advanced_mode:
  preds_df.columns=['id', 'state', 'preds_cases_7', 'preds_cases_3', 'preds_cases']
  preds_df.astype({'preds_cases': 'int'})
  preds_df.astype({'preds_cases_3': 'int'})
  preds_covid19_df=pd.merge(preds_df, covid19_data, on='state', how='left')
  preds_covid19_df=preds_covid19_df.fillna(0)
  preds_covid19_df['preds_cases']=preds_covid19_df['preds_cases'].astype('int')
  preds_covid19_df['preds_cases_3']=preds_covid19_df['preds_cases_3'].astype('int')
  preds_covid19_df['deaths']=preds_covid19_df['deaths'].astype('int')
  del preds_covid19_df['ID']
  del preds_covid19_df['id']
  del preds_covid19_df['discharged']

  merged_preds_data = covid19_json(preds_covid19_df, India_statewise)
  merged_preds_json = merged_preds_data['json_data']
  preds_covid19_data = merged_preds_data['data_frame']

  preds_covid19_geosource=GeoJSONDataSource(geojson=merged_preds_json)

  advanced_covid19_plot = covid19_plot(preds_covid19_geosource, 
                                       input_df=preds_covid19_data,
                                       input_field='preds_cases_3',
                                       enable_advancedStats=True,
                                       plot_title=None)
  advancedPlot_tab = Panel(child=advanced_covid19_plot, title="Advanced")



curdoc().title=app_title
if advanced_mode:
  covid19_tabs = Tabs(tabs=[basicPlot_tab, advancedPlot_tab])
  covid19_layout = covid19_tabs
else:
  covid19_layout = column(basic_covid19_plot)
curdoc().add_root(covid19_layout)