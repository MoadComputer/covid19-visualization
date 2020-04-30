import os
import math
import json
import bokeh
import geopandas
import numpy as np
import pandas as pd

from bokeh.io.doc import curdoc
from bokeh.plotting import figure
from bokeh.models.glyphs import Text
from bokeh.models.widgets import Button
from bokeh.palettes import brewer, OrRd, YlGn
from bokeh.plotting import show as plt_show
from bokeh.tile_providers import Vendors, get_provider
from bokeh.io import output_notebook, show, output_file
from bokeh.layouts import widgetbox, row, column, gridplot
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, NumeralTickFormatter, LinearAxis, Grid, Label
from bokeh.models import ColumnDataSource, Slider, HoverTool, Select, Div, Range1d, WMTSTileSource, BoxZoomTool, TapTool, Panel, Tabs

verbose=False

def apply_corrections(input_df):
  input_df.loc[input_df['state']=='Telengana','state']='Telangana'
  input_df.loc[input_df['state']=='Nagaland#','state']='Nagaland'
  input_df.loc[input_df['state']=='Jharkhand#','state']='Jharkhand'
  return input_df

India_statewise=geopandas.read_file('https://github.com/MoadComputer/covid19-visualization/raw/master/data/GeoJSON_assets/India_statewise_minified.geojson')
India_statewise=India_statewise.to_crs("EPSG:3395")

India_stats=pd.read_csv('https://github.com/MoadComputer/covid19-visualization/raw/master/data/Coronavirus_stats/India/Population_stats_India_statewise.csv')
India_stats=apply_corrections(India_stats)

covid19_data=pd.read_csv('https://github.com/MoadComputer/covid19-visualization/raw/master/data/Coronavirus_stats/India/COVID19_India_statewise.csv')
covid19_data=apply_corrections(covid19_data)

covid19_data=pd.merge(covid19_data, India_stats, on='state', how='left')

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

def CustomPalette(palette_type, enable_colorInverse=True):
  if (palette_type.lower()=='OrRd'.lower()) or (palette_type.lower()=='reds'):
    palette = OrRd[9]
  elif (palette_type.lower()=='YlGn'.lower()) or (palette_type.lower()=='greens'):
    palette = YlGn[9]
  else:
    palette = brewer['Oranges']
    
  if enable_colorInverse:
    palette = palette[::-1]
  else:
    palette = palette[::1]
  return palette

def CustomHoverTool(advanced_hoverTool, custom_hoverTool, performance_hoverTool):
  advancedStats_hover=HoverTool(tooltips ="""<strong><font face="Arial" size="2">@state</font></strong> <br>
                                             <font face="Arial" size="2">Cases: <strong>@total_cases{int}</strong></font><br>
                                             <hr>
                                             <strong><font face="Arial" size="2">Case forecast</font></strong> <br>
                                             <font face="Arial" size="2">+1 day: <strong>@preds_cases{int} (±@preds_cases_std{int})</strong></font><br>
                                             <font face="Arial" size="2">+3 days: <strong>@preds_cases_3{int} (±@preds_cases_3_std{int})</strong></font><br>
                                             <font face="Arial" size="2">+7 days: <strong>@preds_cases_7{int} (±@preds_cases_7_std{int})</strong></font><br>
                                             <hr>  
                                             <strong><font face="Arial" size="1">Forecast by: https://moad.computer</font></strong> <br>""")


  performanceStats_hover=HoverTool(tooltips ="""<strong><font face="Arial" size="2">@state</font></strong> <br>
                                                <hr>
                                                <strong><font face="Arial" size="2">Forecast error</font></strong> <br>
                                                <hr>
                                                <strong><font face="Arial" size="2">Mean absolute percentage</font></strong> <br>
                                                <font face="Arial" size="2">+1 day: <strong>@MAPE{(0.000)}</strong></font><br>
                                                <font face="Arial" size="2">+3 days: <strong>@MAPE_3{(0.000)}</strong></font><br>
                                                <font face="Arial" size="2">+7 days: <strong>@MAPE_7{(0.000)}</strong></font><br>
                                                <hr>  
                                               <strong><font face="Arial" size="1">Forecast by: https://moad.computer</font></strong> <br>""")

  simpleStats_hover=HoverTool(tooltips ="""<strong><font face="Arial" size="3">@state</font></strong> <br>
                                           <font face="Arial" size="3">Cases: @total_cases{int}</font><br>
                                           <font face="Arial" size="3">Deaths: @deaths{int} </font>""")

  standard_hover = HoverTool(tooltips = [('State','@state'),
                                         ('Cases', '@total_cases'),
                                         #('Discharged/migrated', '@discharged'),
                                         ('Deaths', '@deaths')])
  
  if performance_hoverTool:
    hover  = performanceStats_hover
  elif advanced_hoverTool:
    hover = advancedStats_hover
  elif custom_hoverTool:
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

def lakshadweep_correction(plt, input_df=None, advanced_plotting=False):
  if advanced_plotting:
    source = ColumnDataSource(data=dict(x=[8075000],
                                        y=[1250000],
                                        state=['Lakshadweep'],
                                        total_cases=[input_df.loc[input_df['state']=='Lakshadweep','total_cases']],
                                        deaths=[input_df.loc[input_df['state']=='Lakshadweep','deaths']],
                                        preds_cases=[input_df.loc[input_df['state']=='Lakshadweep','preds_cases']],
                                        preds_cases_std=[input_df.loc[input_df['state']=='Lakshadweep','preds_cases_std']],
                                        MAPE=[input_df.loc[input_df['state']=='Lakshadweep','MAPE']],
                                        preds_cases_3=[input_df.loc[input_df['state']=='Lakshadweep','preds_cases_3']],
                                        preds_cases_3_std=[input_df.loc[input_df['state']=='Lakshadweep','preds_cases_3_std']],
                                        MAPE_3=[input_df.loc[input_df['state']=='Lakshadweep','MAPE_3']],
                                        preds_cases_7=[input_df.loc[input_df['state']=='Lakshadweep','preds_cases_7']],
                                        preds_cases_7_std=[input_df.loc[input_df['state']=='Lakshadweep','preds_cases_7_std']],
                                        MAPE_7=[input_df.loc[input_df['state']=='Lakshadweep','MAPE_7']]
                                      ))
  else:
    source = ColumnDataSource(data=dict(x=[8075000],
                                        y=[1250000],
                                        state=['Lakshadweep'],
                                        total_cases=[input_df.loc[input_df['state']=='Lakshadweep','total_cases']],
                                        deaths=[input_df.loc[input_df['state']=='Lakshadweep','deaths']]))

  plt.circle(x='x', y='y', 
             size=25, 
             source=source,
             line_color='purple',
             fill_alpha=0.075,
             color='blue')
  return plt

def create_overlay(plt, x, y, 
                   input_df=None, 
                   advanced_plotting=False):
  overlayText=Label(x=x-950000, y=y-350000, 
                    text="COVID19 in India",
                    text_font_size='25pt')
  plt.add_layout(overlayText) 
  if advanced_plotting:
    source = ColumnDataSource(data=dict(x=[x-125000],
                                        y=[y-230000],
                                        state=['India'],
                                        total_cases=[input_df['total_cases'].sum()],
                                        deaths=[input_df['deaths'].sum()],
                                        preds_cases=[input_df['preds_cases'].sum()],
                                        preds_cases_std=[input_df['preds_cases_std'].sum()],
                                        MAPE=[input_df['MAPE'].mean()],
                                        preds_cases_3=[input_df['preds_cases_3'].sum()],
                                        preds_cases_3_std=[input_df['preds_cases_3_std'].sum()],
                                        MAPE_3=[input_df['MAPE_3'].mean()],
                                        preds_cases_7=[input_df['preds_cases_7'].sum()],
                                        preds_cases_7_std=[input_df['preds_cases_7_std'].sum()],
                                        MAPE_7=[np.mean(np.abs(input_df['MAPE_7']))]
                                       ))
  else:
    source = ColumnDataSource(data=dict(x=[x-125000],
                                        y=[y-230000],
                                        state=['India'],
                                        total_cases=[input_df['total_cases'].sum()],
                                        deaths=[input_df['deaths'].sum()]))

  plt.rect(x='x', y='y', 
           width=1750000, 
           height=500000, 
           color="#CAB2D6",
           source=source,
           line_color='purple',
           #width_units='screen',
           #height_units='screen',
           fill_alpha=0.075)  
  return plt

    
def covid19_plot(covid19_geosource, 
                 input_df=None,
                 input_field=None,
                 color_field='total_cases',
                 plot_title=None,
                 map_overlay=True,
                 palette_type='OrRd',
                 custom_hovertool=True,
                 enable_LakshadweepStats=False,
                 enable_IndiaStats=False,                 
                 enable_advancedStats=False,
                 enable_performanceStats=False,
                 enable_toolbar=False):
  
  palette = CustomPalette(palette_type, enable_colorInverse=False if enable_performanceStats else True)
  color_mapper = LinearColorMapper(palette=palette, 
                                   low=0, 
                                   high=int(10*(np.ceil(np.max(input_df[color_field].values)/10)))\
                                        if not enable_performanceStats else np.round((np.max(input_df[color_field].values)),3)
                                   ) 
  format_tick = NumeralTickFormatter(format=str(input_df[input_field].values.astype('int')) if not enable_performanceStats else\
                                     str(np.round((input_df[input_field].values.astype('float')),1))
                                    )
  color_bar = ColorBar(color_mapper=color_mapper, 
                       label_standoff=11, 
                       formatter=format_tick,
                       border_line_color=None, 
                       major_label_text_font_size='16px',
                       location = (0, 0))
  xmin, xmax, ymin, ymax = MapOverlayFormatter(map_overlay)
  hover = CustomHoverTool(enable_advancedStats, custom_hovertool, enable_performanceStats)

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
                           enableTapTool=True if ((enable_advancedStats) or (enable_performanceStats)) else False )
  
  if enable_LakshadweepStats:
    plt = lakshadweep_correction(plt, 
                                 input_df=input_df, 
                                 advanced_plotting=True if ((enable_advancedStats) or (enable_performanceStats)) else False)

  if enable_IndiaStats:
    plt = create_overlay(plt, xmax, ymax-100000,
                         input_df=input_df, 
                         advanced_plotting=True if ((enable_advancedStats) or (enable_performanceStats)) else False)
  return plt

advanced_mode=True
try:
  preds_df=pd.read_csv('https://github.com/MoadComputer/covid19-visualization/raw/master/data/Coronavirus_stats/India/experimental/output_preds.csv')
  #preds_df=pd.read_csv('./GitHub/MoadComputer/covid19-visualization/data/Coronavirus_stats/India/experimental/output_preds.csv')
except:
  print('Advanced mode disabled ...')
  advanced_mode=False

covid19_geosource=GeoJSONDataSource(geojson=merged_json)
plot_title=None#'COVID19 outbreak in India'
app_title='COVID19 India'

India_totalCases=covid19_data['total_cases'].sum()
India_totalDeaths=covid19_data['deaths'].sum()

basic_covid19_plot = covid19_plot(covid19_geosource, 
                                  input_df=covid19_data,
                                  input_field='total_cases',
                                  color_field='total_cases',
                                  enable_IndiaStats=True,
                                  plot_title=plot_title)
basicPlot_tab = Panel(child=basic_covid19_plot, title=" ■■■ ")

if advanced_mode:
  preds_df.columns=['id', 'state',                                                  \
                    'preds_cases_7', 'preds_cases_3', 'preds_cases',                \
                    'preds_cases_7_std', 'preds_cases_3_std', 'preds_cases_std',    \
                    'MAPE', 'MAPE_3', 'MAPE_7']
  preds_covid19_df=pd.merge(preds_df, covid19_data, 
                            on='state', 
                            how='left')
  preds_covid19_df=preds_covid19_df.fillna(0)
  
  try:
    del preds_covid19_df['ID']
  except:
    print('Unable to delete dataframe item: ID')
  try:
    del preds_covid19_df['id']
  except:
    print('Unable to delete dataframe item: id')
  try:
    del preds_covid19_df['discharged']
  except:
    print('Unable to delete dataframe item: discharged')

  merged_preds_data = covid19_json(preds_covid19_df, India_statewise)
  merged_preds_json = merged_preds_data['json_data']
  preds_covid19_data = merged_preds_data['data_frame']

  preds_covid19_geosource=GeoJSONDataSource(geojson=merged_preds_json)

  advanced_covid19_plot = covid19_plot(preds_covid19_geosource, 
                                       input_df=preds_covid19_data,
                                       input_field='preds_cases_7',
                                       color_field='total_cases',
                                       enable_IndiaStats=True,
                                       enable_advancedStats=True,
                                       plot_title=None)
  advancedPlot_tab = Panel(child=advanced_covid19_plot, title="Advanced")
  
  performance_covid19_plot = covid19_plot(preds_covid19_geosource, 
                                          input_df=preds_covid19_data,
                                          palette_type='Greens',
                                          input_field='MAPE_7',
                                          color_field='MAPE_7',
                                          enable_IndiaStats=True,
                                          enable_performanceStats=True,
                                          plot_title=None)
  performancePlot_tab = Panel(child=performance_covid19_plot, title="Forecast quality")



curdoc().title=app_title
if advanced_mode:
  covid19_tabs = Tabs(tabs=[basicPlot_tab, advancedPlot_tab, performancePlot_tab])
  covid19_layout = covid19_tabs
else:
  covid19_layout = column(basic_covid19_plot)
curdoc().add_root(covid19_layout)