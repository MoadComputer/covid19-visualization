import os
import re
import sys
import math
import json
import bokeh
import geopandas
import numpy as np
import pandas as pd

from scipy.interpolate import interp1d 

from bokeh.io.doc import curdoc
from bokeh.layouts import layout
from bokeh.plotting import figure
from bokeh.models.glyphs import Text
from bokeh.application import Application
from bokeh.models.callbacks import CustomJS
from bokeh.plotting import show as plt_show
from bokeh.palettes import brewer,OrRd,YlGn
from bokeh.models.widgets import Button,Select
from bokeh.tile_providers import Vendors,get_provider
from bokeh.io import output_notebook,show,output_file
from bokeh.application.handlers import FunctionHandler
from bokeh.layouts import widgetbox,row,column,gridplot
from bokeh.models import ColumnDataSource,Slider,HoverTool,Select,Div,Range1d,WMTSTileSource,BoxZoomTool,TapTool,Panel,Tabs
from bokeh.models import GeoJSONDataSource,LinearColorMapper,ColorBar,NumeralTickFormatter,LinearAxis,Grid,Label,Band,Legend,LegendItem

verbose=False
enable_GeoJSON_saving=False
LAST_UPDATE_DATE='06-February-2021'

def apply_corrections(input_df):
  for state in list(input_df['state'].values):
    input_df.loc[input_df['state']==state,'state']=re.sub('[^A-Za-z ]+', '',str(state))
  input_df.loc[input_df['state']=='Telengana','state']='Telangana'  
  input_df.loc[input_df['state']=='Dadra and Nagar Haveli','state']='Dadra and Nagar Haveli and Daman and Diu'
  input_df.loc[input_df['state']=='Dadar Nagar Haveli','state']='Dadra and Nagar Haveli and Daman and Diu'
  input_df.loc[input_df['state']=='Dadra Nagar Haveli','state']='Dadra and Nagar Haveli and Daman and Diu'
  input_df.loc[input_df['state']=='Daman & Diu','state']='Dadra and Nagar Haveli and Daman and Diu'
  input_df.loc[input_df['state']=='Daman and Diu','state']='Dadra and Nagar Haveli and Daman and Diu'
  return input_df

def os_style_formatter(input_str):
  try:
    os_env=os.environ['OS'] 
  except:
    os_env='unknown'
  return str(input_str).replace('/', "\\") if os_env=='Windows_NT' else str(input_str)  

try:
  India_statewise=geopandas.read_file('https://github.com/MoadComputer/covid19-visualization/raw/master/data/GeoJSON_assets/India_statewise_minified.geojson')
  India_stats=pd.read_csv('https://github.com/MoadComputer/covid19-visualization/raw/master/data/Coronavirus_stats/India/Population_stats_India_statewise.csv')
  covid19_data=pd.read_csv('https://github.com/MoadComputer/covid19-visualization/raw/master/data/Coronavirus_stats/India/COVID19_India_statewise.csv')
  preds_df=pd.read_csv('https://github.com/MoadComputer/covid19-visualization/raw/master/data/Coronavirus_stats/India/experimental/output_preds.csv')
except:
  India_GeoJSON_repoFile=os_style_formatter(
      './GitHub/MoadComputer/covid19-visualization/data/GeoJSON_assets/India_statewise_minified.geojson')  
  covid19_statewise_repoFile=os_style_formatter(
      './GitHub/MoadComputer/covid19-visualization/data/Coronavirus_stats/India/COVID19_India_statewise.csv')
  India_statewise_statsFile=os_style_formatter(
      './GitHub/MoadComputer/covid19-visualization/data/Coronavirus_stats/India/Population_stats_India_statewise.csv')
  saved_predsFile=os_style_formatter(
      './GitHub/MoadComputer/covid19-visualization/data/Coronavirus_stats/India/experimental/output_preds.csv') 
    
  if os.path.exists(India_GeoJSON_repoFile):
    India_statewise=geopandas.read_file(India_GeoJSON_repoFile)  
    print('Reading India GeoJSON file from saved repo ...')
  else:
    sys.exit('Failed to read GeoJSON file for India ...')
    
  if os.path.exists(covid19_statewise_repoFile):
    covid19_data=pd.read_csv(covid19_statewise_repoFile)  
    print('Reading India COVID19 file from saved repo ...')
  else:
    sys.exit('Failed to read India COVID19 file ...')
    
  if os.path.exists(India_statewise_statsFile):
    India_stats=pd.read_csv(India_statewise_statsFile)  
    print('Reading India stats file from saved repo ...')
  else:
    sys.exit('Failed to read India stats file ...')
    
  if os.path.exists(saved_predsFile):
    preds_df=pd.read_csv(saved_predsFile)
  else:
    print('Advanced mode disabled ...')
    advanced_mode=False  
    
India_statewise=apply_corrections(India_statewise)
if enable_GeoJSON_saving:
  India_statewise.to_file("India_statewise_minified.geojson", driver='GeoJSON')
India_statewise=India_statewise.to_crs("EPSG:3395")

India_stats=apply_corrections(India_stats)

if len(covid19_data.columns) ==6:
  del covid19_data['active_cases']

covid19_data=apply_corrections(covid19_data)

covid19_data=pd.merge(covid19_data, India_stats, on='state', how='left')
covid19_data_copy=covid19_data.copy()

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
                                             <hr>
                                             <strong><font face="Arial" size="2">Forecast</font></strong> <br>
                                             <font face="Arial" size="2">Reported cases: <strong>@total_cases{}</strong></font>
                                             <font face="Arial" size="2"><p style="color:red; margin:0">+1 day: <strong>@preds_cases{} (±@preds_cases_std{})</strong></p></font>
                                             <font face="Arial" size="2"><p style="color:green; margin:0">+3 days: <strong>@preds_cases_3{} (±@preds_cases_3_std{})</strong></p></font>
                                             <font face="Arial" size="2"><p style="color:blue; margin:0">+7 days: <strong>@preds_cases_7{} (±@preds_cases_7_std{})</strong></p></font>
                                             <hr>  
                                             <strong><font face="Arial" size="1">Updated on: {}</font></strong> <br>
                                             <strong><font face="Arial" size="1">Forecast by: https://moad.computer</font></strong> <br>
                                             """.format('{(0,0)}', 
                                                        '{(0,0)}', 
                                                        '{(0,0)}', 
                                                        '{(0,0)}', 
                                                        '{(0,0)}', 
                                                        '{(0,0)}', 
                                                        '{(0,0)}', 
                                                        LAST_UPDATE_DATE))


  performanceStats_hover=HoverTool(tooltips ="""<strong><font face="Arial" size="2">@state</font></strong> <br>
                                                <hr>
                                                <strong><font face="Arial" size="2">MAPE</font></strong><br>
                                                <strong><font face="Arial" size="1">(Mean Absolute Percentage Error)</font></strong>
                                                <font face="Arial" size="2"><p style="color:red; margin:0">+1 day: <strong>@MAPE{}</strong></p></font>
                                                <font face="Arial" size="2"><p style="color:green; margin:0">+3 days: <strong>@MAPE_3{}</strong></p></font>
                                                <font face="Arial" size="2"><p style="color:blue; margin:0">+7 days: <strong>@MAPE_7{}</strong></p></font>
                                                <hr>  
                                                <strong><font face="Arial" size="1">Updated on: {}</font></strong><br> 
                                                <strong><font face="Arial" size="1">Forecast by: https://moad.computer</font></strong>                                                    
                                              """.format('{(0.000)}', 
                                                         '{(0.000)}', 
                                                         '{(0.000)}',
                                                         LAST_UPDATE_DATE))

  simpleStats_hover=HoverTool(tooltips ="""<strong><font face="Arial" size="3">@state</font></strong> <br>
                                           <font face="Arial" size="3">Cases: @total_cases{}</font><br>
                                           <font face="Arial" size="3">Deaths: @deaths{} </font>
                                           <hr>  
                                           <strong><font face="Arial" size="1">Updated on: {}</font></strong><br> 
                                           <strong><font face="Arial" size="1">Data from: https://mohfw.gov.in </font></strong>                                               
                                        """.format('{(0,0)}', 
                                                   '{(0,0)}',
                                                   LAST_UPDATE_DATE))

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
    xmin = 7570000
    xmax = 10950000
    ymin = 950000
    ymax = 4850000
    
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
    wmts = WMTSTileSource(url="https://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png")
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
              fill_alpha = 0.60 if enableTapTool else 0.65,
              nonselection_alpha = 0.65)
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
             nonselection_alpha=0.20,
             color='blue')
  return plt

def CustomTitleFormatter():
  xtext=8350000
  ytext=4425000
  xbox=9250000
  ybox=4550000
  return xtext, ytext, xbox, ybox

def CustomTitleOverlay(plt,  
                       xtext=0,
                       ytext=0,
                       xbox=0, 
                       ybox=0,
                       input_df=None, 
                       advanced_plotting=False):
  
  overlayText=Label(x=xtext, y=ytext, 
                    text="COVID19 in India",
                    text_font_size='25pt')
    
  plt.add_layout(overlayText) 

  if advanced_plotting:
    print(covid19_data['total_cases'].sum())  
    
    source = ColumnDataSource(data=dict(x=[xbox],
                                        y=[ybox],
                                        state=['India'],
                                        total_cases=[covid19_data['total_cases'].sum()],
                                        deaths=[covid19_data['deaths'].sum()],
                                        preds_cases=[preds_df['preds_cases'].sum()],
                                        preds_cases_std=[preds_df['preds_cases_std'].sum()],
                                        MAPE=[preds_df['MAPE'].mean()],
                                        preds_cases_3=[preds_df['preds_cases_3'].sum()],
                                        preds_cases_3_std=[preds_df['preds_cases_3_std'].sum()],
                                        MAPE_3=[preds_df['MAPE_3'].mean()],
                                        preds_cases_7=[preds_df['preds_cases_7'].sum()],
                                        preds_cases_7_std=[preds_df['preds_cases_7_std'].sum()],
                                        MAPE_7=[np.mean(np.abs(preds_df['MAPE_7']))]
                                       ))
  else:
    source = ColumnDataSource(data=dict(x=[xbox],
                                        y=[ybox],
                                        state=['India'],
                                        total_cases=[input_df['total_cases'].sum()],
                                        deaths=[input_df['deaths'].sum()]))

  plt.rect(x='x', y='y', 
           width=2250000, 
           height=250000, 
           color="#CAB2D6",
           source=source,
           line_color='purple',
           #width_units='screen',
           #height_units='screen',
           fill_alpha=0.25)  
  return plt

    
def covid19_plot(covid19_geosource,
                 input_df=None,
                 input_field=None,
                 color_field='total_cases',
                 plot_title=None,
                 map_overlay=True,
                 palette_type='OrRd',
                 integer_plot=False,
                 custom_hovertool=True,
                 enable_LakshadweepStats=True,
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
  if integer_plot:
    format_tick=NumeralTickFormatter(format='0,0')
  else:
    format_tick=NumeralTickFormatter(format=str(input_df[input_field].values.astype('int')) if not enable_performanceStats else\
                                     str(np.round((input_df[input_field].values.astype('float')),1)))
  color_bar = ColorBar(color_mapper=color_mapper, 
                       label_standoff=15, 
                       formatter=format_tick,
                       border_line_color=None, 
                       major_label_text_font_size='14px',
                       location = (0, 0))
  xmin,xmax,ymin,ymax=MapOverlayFormatter(map_overlay)
  hover=CustomHoverTool(enable_advancedStats,custom_hovertool,enable_performanceStats)

  plt=figure(title = plot_title,
             x_range=(xmin, xmax) if map_overlay else None,
             y_range=(ymin, ymax) if map_overlay else None,
             tools='save' if enable_toolbar else '', 
             plot_height = 580, plot_width = 580,
             toolbar_location = 'left' if enable_toolbar else None,
             lod_factor=int(1e7),
             lod_threshold=int(2),
             # output_backend="webgl"
            ) 
        
  plt=geographic_overlay(plt, 
                         geosourceJson=covid19_geosource,
                         colorBar=color_bar,
                         colorMapper=color_mapper,
                         colorMode=input_field,
                         hoverTool=hover,
                         mapOverlay=map_overlay,
                         enableToolbar=enable_toolbar,
                         enableTapTool=True if ((enable_advancedStats) or (enable_performanceStats)) else False)
  
  if enable_LakshadweepStats:
    plt=lakshadweep_correction(plt, 
                               input_df=input_df, 
                               advanced_plotting=True if ((enable_advancedStats) or (enable_performanceStats)) else False)

  if enable_IndiaStats:
    xtext,ytext,xbox,ybox=CustomTitleFormatter()
    plt=CustomTitleOverlay(plt, 
                           xtext=xtext,
                           ytext=ytext,
                           xbox=xbox, 
                           ybox=ybox,
                           input_df=input_df, 
                           advanced_plotting=True if ((enable_advancedStats) or (enable_performanceStats)) else False)
  plt.xaxis.major_tick_line_color=None  
  plt.yaxis.major_tick_line_color=None
  plt.xaxis.minor_tick_line_color=None 
  plt.yaxis.minor_tick_line_color=None 
  plt.xaxis[0].ticker.num_minor_ticks=0
  plt.yaxis[0].ticker.num_minor_ticks=0
  plt.yaxis.formatter=NumeralTickFormatter(format='0,0')
  return plt

advanced_mode=True

covid19_geosource=GeoJSONDataSource(geojson=merged_json)
plot_title=None#'COVID19 outbreak in India'
app_title='COVID19 India'

India_totalCases=covid19_data['total_cases'].sum()
India_totalDeaths=covid19_data['deaths'].sum()
print(India_totalCases)

basic_covid19_plot = covid19_plot(covid19_geosource, 
                                  input_df=covid19_data,
                                  input_field='total_cases',
                                  color_field='total_cases',
                                  enable_IndiaStats=True,
                                  integer_plot=True,
                                  plot_title=plot_title)
basicPlot_tab = Panel(child=basic_covid19_plot, title=" ■■■ ")

if advanced_mode:
  preds_df.columns=['id','state',                                                   \
                    'preds_cases_7', 'preds_cases_3', 'preds_cases',                \
                    'preds_cases_7_std', 'preds_cases_3_std', 'preds_cases_std',    \
                    'MAPE', 'MAPE_3', 'MAPE_7']
  print(preds_df.head(10))
  print(covid19_data_copy.head(10))
  preds_covid19_df=pd.merge(covid19_data_copy, preds_df, 
                            on='state', 
                            how='left')
  preds_covid19_df=preds_covid19_df.fillna(0)
  print(preds_covid19_df.head(10))
  
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

  merged_preds_data=covid19_json(preds_covid19_df,India_statewise)
  merged_preds_json=merged_preds_data['json_data']
  preds_covid19_data=merged_preds_data['data_frame']
  print(preds_covid19_data['state'].equals(covid19_data['state']))
  print(set(list(preds_covid19_data['state']))-set(list(covid19_data['state'])))  
  preds_covid19_geosource=GeoJSONDataSource(geojson=merged_preds_json)

  advanced_covid19_plot=covid19_plot(preds_covid19_geosource, 
                                     input_df=preds_covid19_data,
                                     input_field='preds_cases_7',
                                     color_field='total_cases',
                                     enable_IndiaStats=True,
                                     enable_advancedStats=True,
                                     integer_plot=True,
                                     plot_title=None)
  advancedPlot_tab=Panel(child=advanced_covid19_plot, title="Forecast")
  
  performance_covid19_plot=covid19_plot(preds_covid19_geosource, 
                                        input_df=preds_covid19_data,
                                        palette_type='Greens',
                                        input_field='MAPE_7',
                                        color_field='MAPE_7',
                                        enable_IndiaStats=True,
                                        enable_performanceStats=True,
                                        plot_title=None)
  performancePlot_tab=Panel(child=performance_covid19_plot,title="Forecast quality")

def LineSmoothing(x,y, 
                  interpolationType='cubic',
                  interpolationPoints=1000):
  fn=interp1d(x,y, 
              kind=interpolationType)
  x_=np.linspace(np.min(x), np.max(x), 
                 interpolationPoints)
  y_=fn(x_)
  return x_,y_

def model_performancePlot(source, 
                          use_cds=False,
                          enable_interpolation=False, 
                          custom_perfHoverTool=True):
    if use_cds:
      plotIndex=source.data['plot_index']
      plotIndex_labels=source.data['plot_labels']
      dateLabels={i: date for i, date in enumerate(plotIndex_labels)}
      x=source.data['x']
    else:
      plotIndex_labels=list(source['date'].astype('str'))  
      modelPerformance=source.dropna()  
      x=[i for i in range(len(list(source['date'].astype('str'))))]

      y_cases=list(source['total_cases'].astype('int'))
      y_preds=list(source['preds_cases'].astype('int'))
      y_preds3=list(source['preds_cases_3'].astype('int'))
      y_preds7=list(source['preds_cases_7'].astype('int'))

      y_stdev=list(source['preds_cases_std'].astype('int'))
      y_3_stdev=list(source['preds_cases_3_std'].astype('int'))
      y_7_stdev=list(source['preds_cases_7_std'].astype('int'))

      lower_lim=list(np.asarray(y_preds)-3*np.asarray(y_stdev))
      lower_3_lim=list(np.asarray(y_preds3)-3*np.asarray(y_3_stdev))
      lower_7_lim=list(np.asarray(y_preds7)-3*np.asarray(y_7_stdev))

      upper_lim=list(np.asarray(y_preds)+3*np.asarray(y_stdev))
      upper_3_lim=list(np.asarray(y_preds3)+3*np.asarray(y_3_stdev))
      upper_7_lim=list(np.asarray(y_preds7)+3*np.asarray(y_7_stdev))

      plotIndex=list(source['date'].astype('str'))
      dateLabels={i: date for i, date in enumerate(plotIndex)}
      source=ColumnDataSource({'x':x,'plot_index':plotIndex,'plot_labels':plotIndex_labels, 
                               'y_cases':y_cases,'y_preds':y_preds,'y_preds3':y_preds3,'y_preds7':y_preds7,
                               'y_std':y_stdev,'y_3std':y_3_stdev,'y_7std':y_7_stdev,
                               'upper_lim':upper_lim,'upper_3_lim':upper_3_lim,'upper_7_lim':upper_7_lim,
                               'lower_lim':lower_lim,'lower_3_lim':lower_3_lim,'lower_7_lim':lower_7_lim})
    
    if enable_interpolation:
      x_cases_interpol,y_cases_interpol=LineSmoothing(x,y_cases)
      x_preds_interpol,y_preds_interpol=LineSmoothing(x,y_preds)
      x_preds3_interpol,y_preds3_interpol=LineSmoothing(x,y_preds3) 
      x_preds7_interpol,y_preds7_interpol=LineSmoothing(x,y_preds7)

    if len(plotIndex)%2==0 or len(plotIndex)%5==0 or np.round((len(plotIndex)/10)/(len(plotIndex)//10))==1:
      for i in range(
                  len(plotIndex)//2
                    ):
        dateLabelObject=datetime.strptime(str(dateLabels[len(plotIndex)-1]),'%d-%B-%Y')
        dateLabel_extra=dateLabelObject+timedelta(days=(i+1))
        dateLabels.update({len(plotIndex)+i:str(dateLabel_extra.strftime('%d-%B-%Y')) })

    data_cases=dict(title=['report' \
                           for i in range(len(x))],
                    plotIndex=plotIndex,
                    x='x',
                    y='y_cases',
                    source=source)
    data_preds=dict(title=['forecast a day before'\
                           for i in range(len(x))],
                    plotIndex='plot_index',
                    x='x',
                    y='y_preds',
                    source=source)
    data_preds3=dict(title=['forecast 3 days before'\
                            for i in range(len(x))],
                     plotIndex='plot_index',
                     x='x',
                     y='y_preds3',
                     source=source)
    data_preds7=dict(title=['forecast 7 days before'\
                            for i in range(len(x))],
                     plotIndex='plot_index',
                     x='x',
                     y='y_preds7',
                     source=source)

    TOOLTIPS = """<strong><font face="Arial" size="2">Forecast performance for @plot_index</font></strong> <br>
                  <font face="Arial" size="2"><p style="color:black; margin:0">Reported cases: <strong>@y_cases{}</strong></p></font>
                  <font face="Arial" size="2"><p style="color:red; margin:0">Forecast a day ago: <strong>@y_preds{} (±@y_std{})</strong></p></font> 
                  <font face="Arial" size="2"><p style="color:green; margin:0">Forecast 3 days ago: <strong>@y_preds3{} (±@y_3std{})</strong></p></font>
                  <font face="Arial" size="2"><p style="color:blue; margin:0">Forecast 7 days ago: <strong>@y_preds7{} (±@y_7std{})</strong></p></font>
                  <hr>
                  <strong><font face="Arial" size="1">Updated on: {}</font></strong><br> 
                  <strong><font face="Arial" size="1">Forecast by: https://moad.computer</font></strong>""".format('{(0,0)}',
                                                                                                                   '{(0,0)}',
                                                                                                                   '{(0,0)}',
                                                                                                                   '{(0,0)}',
                                                                                                                   '{(0,0)}',
                                                                                                                   '{(0,0)}',
                                                                                                                   '{(0,0)}',
                                                                                                                    LAST_UPDATE_DATE)           \
               if custom_perfHoverTool else [('Date: ','@plot_index'),
                                             ('Cases: ','@y_cases')]

    perfPlot=figure(#y_axis_type="log",y_range=(2.5e4,7.5e4), 
                    plot_height=530, plot_width=530,
                    tools='hover', 
                    toolbar_location=None,
                    tooltips=TOOLTIPS)
    perfPlot.line(x='x',y='y_cases',
                  source=source,
                  line_width=2.5, 
                  color='black')
    r = perfPlot.circle(x='x', y='y_cases', 
                   color='grey', 
                   fill_color='black',
                   size=8, 
                   source=source)

    perfPlot.line(x='x',y='y_preds',
                  source=source,
                  color='darkred')
    r1 = perfPlot.circle(x='x', y='y_preds', 
                    color='darkred', 
                    fill_color='red',
                    size=8, 
                    source=source)

    perfPlot.line(x='x',y='y_preds3',
                  source=source,
                  color='green')
    r3 = perfPlot.circle(x='x', y='y_preds3', 
                    color='lime', 
                    fill_color='darkgreen', 
                    size=8,
                    source=source)

    perfPlot.line(x='x',y='y_preds7', 
                  source=source,
                  color='blue')
    r7=perfPlot.circle(x='x', y='y_preds7', 
                       color='purple', 
                       fill_color='blue', 
                       size=8,
                       source=source)
 
    #x_ul_interpol,ul_interpol=LineSmoothing(x,upper_lim)
    #x_ll_interpol,ll_interpol=LineSmoothing(x,lower_lim)
    #src_interpol=ColumnDataSource({'x_ul_interpol':x_ul_interpol,'ul_interpol':ul_interpol,
    #                               'x_ll_interpol':x_ll_interpol,'ll_interpol':ll_interpol})
    
    #ul=perfPlot.line(x='x_ul_interpol',
    #                 y='ul_interpol',
    #                 source=src_interpol,
    #                 color='pink')
    #ll=perfPlot.line(x='x_ll_interpol',
    #                 y='ll_interpol',
    #                 source=src_interpol,
    #                 color='pink')

    perfPlot.hover.renderers=[r,r1,r3,r7]
    
    perfPlot.yaxis.formatter.use_scientific=False
    perfPlot.yaxis.formatter=NumeralTickFormatter(format='0,0')
    
    perfPlot.xaxis.major_label_overrides=dateLabels
    perfPlot.xaxis.axis_label='Date'
    perfPlot.yaxis.axis_label='COVID19 cases'
    perfPlot.xaxis.major_label_orientation=(math.pi*.75)/2

    band=Band(base='x',lower='lower_lim',upper='upper_lim',source=source, 
              level='underlay',fill_alpha=0.5,line_width=1,
              fill_color='indianred',line_color='indianred')
    band3=Band(base='x',lower='lower_3_lim',upper='upper_3_lim',source=source, 
               level='underlay',fill_alpha=0.4,line_width=1,
               fill_color='lime',line_color='lime')
    band7=Band(base='x',lower='lower_7_lim',upper='upper_7_lim',source=source, 
               level='underlay',fill_alpha=0.25,line_width=1,
               fill_color='indigo',line_color='indigo')

    perfPlot.renderers.append(band)
    perfPlot.renderers.append(band3)
    perfPlot.renderers.append(band7)
    return perfPlot

from datetime import datetime, timedelta
def date_formatter(x):
  datetimeobject = datetime.strptime(str(x),'%Y%m%d')
  return datetimeobject.strftime('%d-%B-%Y')

def make_dataset(state):
  DATA_SOURCE='https://github.com/MoadComputer/covid19-visualization/raw/master/data/Coronavirus_stats/India/experimental/model_performance_'
  DATA_URL='{}{}.csv'.format(DATA_SOURCE,
                             state)
  DATA_URL=DATA_URL.replace(" ", "%20")
  DATA_FILE=os_style_formatter(
        './GitHub/MoadComputer/covid19-visualization/data/Coronavirus_stats/India/experimental/model_performance_{}.csv'.format(
            state))
  try:
    modelPerformance=pd.read_csv(DATA_URL)
    print('Reading model performance for: {} from URL ...'.format(state))
  except:
    if os.path.exists(DATA_FILE):
      modelPerformance=pd.read_csv(DATA_FILE)  
      print('Reading model performance for: {} from saved repo ...'.format(state))
    else:
      sys.exit('No statewise model performance file found ...')      
  modelPerformance['date']=modelPerformance['date'].apply(lambda x: date_formatter(x))  
  plotIndex_labels=list(modelPerformance['date'].astype('str'))
  
  modelPerformance=modelPerformance.dropna()
  plotIndex=list(modelPerformance['date'].astype('str'))   
    
  x=[i for i in range(len(list(modelPerformance['date'].astype('str'))))]

  y_cases=list(modelPerformance['total_cases'].astype('int'))

  y_preds=list(modelPerformance['preds_cases'].astype('int'))
  y_preds3=list(modelPerformance['preds_cases_3'].astype('int'))
  y_preds7=list(modelPerformance['preds_cases_7'].astype('int'))

  y_std=list(modelPerformance['preds_cases_std'].astype('int'))
  y_3std=list(modelPerformance['preds_cases_3_std'].astype('int'))
  y_7std=list(modelPerformance['preds_cases_7_std'].astype('int'))
      
  lower_lim=list(np.asarray(y_preds)-3*np.asarray(y_std))
  lower_3_lim=list(np.asarray(y_preds3)-3*np.asarray(y_3std))
  lower_7_lim=list(np.asarray(y_preds7)-3*np.asarray(y_7std))

  upper_lim=list(np.asarray(y_preds)+3*np.asarray(y_std))
  upper_3_lim=list(np.asarray(y_preds3)+3*np.asarray(y_3std))
  upper_7_lim=list(np.asarray(y_preds7)+3*np.asarray(y_7std))

  return ColumnDataSource({'x':x, 'y_cases':y_cases, 
                           'plot_index': plotIndex, 'plot_labels':plotIndex_labels, 
                           'y_preds':y_preds, 'y_preds3':y_preds3, 'y_preds7':y_preds7,
                           'y_std':y_std, 'y_3std':y_3std,'y_7std':y_7std,
                           'upper_lim':upper_lim,'upper_3_lim':upper_3_lim,'upper_7_lim':upper_7_lim,
                           'lower_lim':lower_lim,'lower_3_lim':lower_3_lim,'lower_7_lim':lower_7_lim})

def update_plot(attrname, old, new):
  updated_data=make_dataset(state_select.value) 
  source.data.update(updated_data.data)

curdoc().title=app_title
if advanced_mode:
  try:
    modelPerformance=pd.read_csv('https://github.com/MoadComputer/covid19-visualization/raw/master/data/Coronavirus_stats/India/experimental/model_performance_India.csv')
  except:
    India_modelPerformance_file=os_style_formatter(
        './GitHub/MoadComputer/covid19-visualization/data/Coronavirus_stats/India/experimental/model_performance_India.csv')
    if os.path.exists(India_modelPerformance_file):
      modelPerformance=pd.read_csv(India_modelPerformance_file)
      print('Reading India model performance file from saved repo ...')      
    else:
      print('Failed to read India model performance file ...')        
  modelPerformance['date']=modelPerformance['date'].apply(lambda x: date_formatter(x))
  model_perfPlot=model_perfPlot=model_performancePlot(modelPerformance)  
  modelPerformance_tab=Panel(child=model_perfPlot,title="Forecast performance") 
    
  stateList=list(preds_df['state'])  
  stateList.append('India')
  state_select=Select(value='India',title='Select region or state: ',options=sorted(stateList))
    
  source=make_dataset('India')
  state_select.on_change('value',update_plot) 
  statewise_plot=model_performancePlot(source,use_cds=True)
  
  statewise_layout=column(state_select,statewise_plot) 
  statewisePerf_tab=Panel(child=statewise_layout,title='Forecast performance') 

  covid19_tabs = Tabs(tabs=[basicPlot_tab, 
                            advancedPlot_tab, 
                            performancePlot_tab, 
                            #modelPerformance_tab, 
                            statewisePerf_tab])
  covid19_layout = covid19_tabs 
else:
  covid19_layout = column(basic_covid19_plot)
curdoc().add_root(covid19_layout)