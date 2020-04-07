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
from bokeh.io import output_notebook, show, output_file
from bokeh.layouts import widgetbox, row, column, gridplot
from bokeh.tile_providers import Vendors, get_provider
from bokeh.models import Slider, HoverTool, Select, Div, Range1d, WMTSTileSource
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, NumeralTickFormatter

India_statewise = geopandas.read_file('https://github.com/MoadComputer/covid19-visualization/raw/master/data/GeoJSON_assets/India_statewise_minified.geojson')
India_statewise.crs = {'init': 'epsg:4326'}
India_statewise.head()

covid19_data = pd.read_csv('https://github.com/MoadComputer/covid19-visualization/raw/master/data/India_statewise/COVID19_India_statewise.csv')
covid19_data.head()

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
                 plot_title=None):
  palette = brewer['Oranges'][8]
  palette = palette[::-1]
  hover = HoverTool(tooltips = [('State','@state'),
                                ('Total cases', '@total_cases'),
                                ('Total discharged/migrated', '@discharged'),
                                ('Total deaths', '@deaths')])
  color_mapper = LinearColorMapper(palette = palette, 
                                   low = 0, 
                                   high = int(10*(np.ceil(np.max(input_df[input_field].values)/10))))
  format_tick = NumeralTickFormatter(format=str(input_df[input_field].values))
  color_bar = ColorBar(color_mapper=color_mapper, 
                       label_standoff=10, 
                       formatter=format_tick,
                       border_line_color=None, 
                       location = (0, 0))
  plt = figure(title = plot_title,
               tools='save', 
               plot_height = 640, plot_width = 640,
               toolbar_location = 'left',
               lod_factor=int(1e7),
               #lod_threshold=int(2),
               #output_backend="webgl"
             )
  plt.xgrid.grid_line_color = None
  plt.ygrid.grid_line_color = None
  plt.axis.visible = False
  plt.patches('xs','ys', 
            source = covid19_geosource, 
            fill_color = {'field' : 'deaths', 
                          'transform' : color_mapper},
            line_color = 'red', 
            line_width = 1.25, 
            fill_alpha = 1)
  plt.add_layout(color_bar, 'right')
  plt.add_tools(hover)
  plt.title.text_font_size = '20pt'
  return plt

covid19_geosource=GeoJSONDataSource(geojson=merged_json)

plot_title='COVID-19 outbreak in India'
app_title='COVID19 India'
_covid19_plot = covid19_plot(covid19_geosource, 
                             input_df=covid19_data,
                             input_field='deaths',
                             plot_title=plot_title)
curdoc().title=app_title
covid19_layout = column(_covid19_plot)
curdoc().add_root(covid19_layout)