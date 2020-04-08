import os
import math
import json
import bokeh
import geopandas
import pandas as pd
import numpy as np

from bokeh.io.doc import curdoc
from bokeh.palettes import brewer
from bokeh.plotting import figure
from bokeh.plotting import show as plt_show
from bokeh.tile_providers import Vendors, get_provider
from bokeh.io import output_notebook, show, output_file
from bokeh.layouts import widgetbox, row, column, gridplot
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, NumeralTickFormatter
from bokeh.models import Slider, HoverTool, Select, Div, Range1d, WMTSTileSource, BoxZoomTool

India_statewise = geopandas.read_file('https://github.com/MoadComputer/covid19-visualization/raw/master/data/GeoJSON_assets/India_statewise_minified.geojson')
India_statewise = India_statewise.to_crs("EPSG:3395")

covid19_data = pd.read_csv('https://github.com/MoadComputer/covid19-visualization/raw/master/data/India_statewise/COVID19_India_statewise.csv')
covid19_data.loc[covid19_data['state'] == 'Telengana', 'state'] = 'Telangana'

noCOVID19_list = list(set(list(India_statewise.state.values)) -set(list(covid19_data.state)))
print('A total of: {} states with no reports of COVID19 ...'.format(len(noCOVID19_list)))
print('\nStates in India with no COVID19 reports:')
for noCOVID19_state in noCOVID19_list:
  print('\n{} ...'.format(noCOVID19_state))

def covid19_json(covid_df, geo_df):
    merged_df = pd.merge(geo_df, covid_df, on='state', how='left')
    merged_df = merged_df.fillna(0)
    merged_json = json.loads(merged_df.to_json())
    json_data = json.dumps(merged_json)
    return {'json_data': json_data, 'data_frame': merged_df}

merged_data = covid19_json(covid19_data, India_statewise)
merged_json = merged_data['json_data']

def covid19_plot(covid19_geosource, 
                 input_df=None,
                 input_field=None,
                 plot_title=None,
                 map_overlay=True,
                 enable_toolbar=False):
  palette = brewer['Oranges'][8]
  palette = palette[::-1]
  hover = HoverTool(tooltips = [('State','@state'),
                                ('Cases', '@total_cases'),
                                #('Discharged/migrated', '@discharged'),
                                ('Deaths', '@deaths')])
  color_mapper = LinearColorMapper(palette = palette, 
                                   low = 0, 
                                   high = int(10*(np.ceil(np.max(input_df[input_field].values)/10))))
  format_tick = NumeralTickFormatter(format=str(input_df[input_field].values))
  color_bar = ColorBar(color_mapper=color_mapper, 
                       label_standoff=10, 
                       formatter=format_tick,
                       border_line_color=None, 
                       major_label_text_font_size='16px',
                       location = (0, 0))
  if map_overlay:
    xmin = 8450000
    xmax = 10000000
    ymin = 850000
    ymax = 4550000
  plt = figure(title = plot_title,
               x_range=(xmin, xmax) if map_overlay else None,
               y_range=(ymin, ymax) if map_overlay else None,
               tools='save' if enable_toolbar else '', 
               plot_height = 640, plot_width = 640,
               toolbar_location = 'left' if enable_toolbar else None,
               #lod_factor=int(1e7),
               #lod_threshold=int(2),
               output_backend="webgl"
               )
  if map_overlay:
    wmts = WMTSTileSource(url="http://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png")
    plt.add_tile(wmts)
    plt.xaxis.axis_label = 'longitude'
    plt.yaxis.axis_label = 'latitude'
  plt.xgrid.grid_line_color = None
  plt.ygrid.grid_line_color = None
  plt.axis.visible = False
  plt.patches('xs','ys', 
              source = covid19_geosource, 
              fill_color = {'field' : 'deaths', 
                            'transform' : color_mapper},
              line_color = 'purple', 
              line_width = 0.5, 
              fill_alpha = 0.85)
  plt.add_layout(color_bar, 'right')
  plt.add_tools(hover)
  plt.title.text_font_size = '34pt'
  return plt

covid19_geosource=GeoJSONDataSource(geojson=merged_json)

plot_title='COVID19 outbreak in India'
app_title='COVID19 India'
_covid19_plot = covid19_plot(covid19_geosource, 
                             input_df=covid19_data,
                             input_field='deaths',
                             plot_title=plot_title)
curdoc().title=app_title
covid19_layout = column(_covid19_plot)
curdoc().add_root(covid19_layout)