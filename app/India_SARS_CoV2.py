import os, re, sys, math, json, bokeh, geopandas, \
       numpy as np, pandas as pd

from jinja2 import Template
from packaging import version
from bokeh.themes import Theme
from bokeh.io.doc import curdoc
from bokeh.layouts import layout
from bokeh.plotting import figure
from bokeh.models.glyphs import Text
from scipy.interpolate import interp1d
from datetime import datetime, timedelta
from bokeh.application import Application
from bokeh.models.callbacks import CustomJS
from bokeh.plotting import show as plt_show
from bokeh.palettes import brewer, OrRd, YlGn
from bokeh.models.widgets import Button, Select
from bokeh.io import output_notebook, show, output_file
from bokeh.application.handlers import FunctionHandler
from bokeh.plotting import save, figure, output_file as out_file
from bokeh.models import ColumnDataSource, Slider, HoverTool, InlineStyleSheet,              \
                         Select, Div, Range1d, WMTSTileSource, BoxZoomTool, TapTool, Tabs
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar,                     \
                         NumeralTickFormatter, LinearAxis, Grid, Label, Band,                \
                         Legend, LegendItem

bokeh_version = bokeh.__version__ 
bokeh_version_msg = 'Generating SARS-CoV2 state-wise statistics overlay for India using Bokeh visualization library version: '

print(bokeh_version_msg, bokeh_version)

version_check = version.parse(bokeh_version) >= version.parse('3.4.1')

if version_check:
    from bokeh.models import TabPanel as Tab_Panel
    from bokeh.layouts import column as Column_Layout
else:
    try:
        from bokeh.models import Panel as Tab_Panel
        from bokeh.layouts import column as Column_Layout
    except ImportError:
        try:
            from bokeh.models import TabPanel as Tab_Panel
            from bokeh.models.layouts import Column_Layout
        except Exception as e:
            e = getattr(e, 'message', repr(e))
            raise ValueError(f'Failed Bokeh imports due to: {e} ...')

verbose = False
enable_GeoJSON_saving = False

DATA_UPDATE_DATE = '06-February-2026'
FORECASTS_UPDATE_DATE = '06-February-2026'

DATA_URL = 'https://raw.githubusercontent.com/MoadComputer/covid19-visualization/main/data'
LOCAL_DATA_DIR = './GitHub/MoadComputer/covid19-visualization/data'
ALT_LOCAL_DATA_DIR = '../data'

GEOJSON_FILENAME = 'India_statewise.geojson'
POPUL_STATS_CSV_FILENAME = 'Population_stats_India_statewise.csv'
SARSCOV2_STATS_CSV_FILENAME = 'India_SARS_CoV2_statewise.csv'
SARSCOV2_FORECASTS_FILENAME = 'output_preds.csv'

GEOJSON_FILENAME_POINTER_STR = f'/GeoJSON_assets/{GEOJSON_FILENAME}'
POPUL_STATS_CSV_FILENAME_POINTER_STR = f'/Coronavirus_stats/India/{POPUL_STATS_CSV_FILENAME}'
SARSCOV2_STATS_CSV_FILENAME_POINTER_STR = f'/Coronavirus_stats/India/{SARSCOV2_STATS_CSV_FILENAME}'
SARSCOV2_FORECASTS_FILENAME_POINTER_STR = f'/Coronavirus_stats/India/experimental/{SARSCOV2_FORECASTS_FILENAME}'
PERF_FILENAME_POINTER_STR = '/Coronavirus_stats/India/experimental/model_performance_'

PLOT_FONT = 'times' # 'arial' #

HTML_FONT = 'Times New Roman' # 'Serif' # 
HTML_INT_FORMATTER_STR = '{(0,0)}'
HTML_FLOAT_FORMATTER_STR = '{(0.000)}'

def apply_corrections(input_df:'Pandas dataframe')->'Pandas dataframe':
  for state in list(input_df['state'].values):
    input_df.loc[input_df['state']==state,'state']=re.sub('[^A-Za-z ]+', '',str(state))
  input_df.loc[input_df['state']=='Karanataka','state']='Karnataka' 
  input_df.loc[input_df['state']=='Himanchal Pradesh','state']='Himachal Pradesh' 
  input_df.loc[input_df['state']=='Telengana','state']='Telangana'  
  input_df.loc[input_df['state']=='Dadra and Nagar Haveli','state']='Dadra and Nagar Haveli and Daman and Diu'
  input_df.loc[input_df['state']=='Dadar Nagar Haveli','state']='Dadra and Nagar Haveli and Daman and Diu'
  input_df.loc[input_df['state']=='Dadra Nagar Haveli','state']='Dadra and Nagar Haveli and Daman and Diu'
  input_df.loc[input_df['state']=='Daman & Diu','state']='Dadra and Nagar Haveli and Daman and Diu'
  input_df.loc[input_df['state']=='Daman and Diu','state']='Dadra and Nagar Haveli and Daman and Diu'
  return input_df

def os_style_formatter(input_str:str)->str:
  try:
    os_env = os.environ['OS'] 
  except Exception as e:
    os_env = 'unknown'
    e = getattr(e, 'message', repr(e))
    print(f'Failed to detect the OS environment due to: {e} ...')
  return str(input_str).replace('/', "\\") if os_env=='Windows_NT' else str(input_str)  

try:
  India_statewise = geopandas.read_file(f'{DATA_URL}{GEOJSON_FILENAME_POINTER_STR}')
  India_stats = pd.read_csv(f'{DATA_URL}{POPUL_STATS_CSV_FILENAME_POINTER_STR}')
  sars_cov2_data = pd.read_csv(f'{DATA_URL}{SARSCOV2_STATS_CSV_FILENAME_POINTER_STR}')
  preds_df = pd.read_csv(f'{DATA_URL}{SARSCOV2_FORECASTS_FILENAME_POINTER_STR}')
except Exception as e:
  e = getattr(e, 'message', repr(e))
  print(f'Failed reading URL data due to: {e} ...')
  if os.path.exists(os_style_formatter(ALT_LOCAL_DATA_DIR)):
    LOCAL_DATA_DIR = ALT_LOCAL_DATA_DIR
  India_GeoJSON_repoFile = os_style_formatter(
      f'{LOCAL_DATA_DIR}{GEOJSON_FILENAME_POINTER_STR}'
  ) 
  sars_cov2_statewise_repoFile = os_style_formatter(
      f'{LOCAL_DATA_DIR}{SARSCOV2_STATS_CSV_FILENAME_POINTER_STR}'
  )
  India_statewise_statsFile = os_style_formatter(
      f'{LOCAL_DATA_DIR}{POPUL_STATS_CSV_FILENAME_POINTER_STR}'
  )
  saved_predsFile = os_style_formatter(
      f'{LOCAL_DATA_DIR}{SARSCOV2_FORECASTS_FILENAME_POINTER_STR}'
  ) 

  if os.path.exists(India_GeoJSON_repoFile):
    India_statewise = geopandas.read_file(India_GeoJSON_repoFile)  
    print('Reading India GeoJSON file from saved repo ...')
  else:
    sys.exit('Failed to read GeoJSON file for India ...')

  if os.path.exists(sars_cov2_statewise_repoFile):
    sars_cov2_data = pd.read_csv(sars_cov2_statewise_repoFile)  
    print('Reading India SARS-CoV2 file from saved repo ...')
  else:
    sys.exit('Failed to read India SARS-CoV2 file ...')

  if os.path.exists(India_statewise_statsFile):
    India_stats = pd.read_csv(India_statewise_statsFile)  
    print('Reading India stats file from saved repo ...')
  else:
    sys.exit('Failed to read India stats file ...')

  if os.path.exists(saved_predsFile):
    preds_df = pd.read_csv(saved_predsFile)
  else:
    print('Advanced mode disabled ...')
    advanced_mode=False

sars_cov2_data.fillna(0)

preds_df = preds_df[
  ['state',                                                        \
   'preds_cases_7', 'preds_cases_3', 'preds_cases',                \
   'preds_cases_7_std', 'preds_cases_3_std', 'preds_cases_std',    \
   'MAPE', 'MAPE_3', 'MAPE_7']
]

preds_df.fillna(0)

India_statewise = apply_corrections(India_statewise)

def convert_multi_polygon_to_list(state, input_df):
    polygon_arr = np.array(
      input_df[input_df['state'] == state]['geometry']
    )
    return list(polygon_arr[0].geoms)

def update_polygon_geojson_dataframe(state, input_df):
    polygon_list = convert_multi_polygon_to_list(state, input_df)
    print(f'Number of polygons from Multipolygon for: {state}: ', len(polygon_list))
    for p_idx, polygon in enumerate(polygon_list):
        if p_idx == 0:
            input_df.loc[input_df['state'] == state,'geometry'] = polygon
        else:
            input_df.loc[len(input_df) + 1] = [state, polygon]
    return input_df

India_statewise = India_statewise.to_crs(
   'EPSG:3857'
  #'EPSG:3395'
)

state = 'Puducherry'
India_statewise = update_polygon_geojson_dataframe(state, India_statewise)

state = 'Andaman and Nicobar Islands'
India_statewise = update_polygon_geojson_dataframe(state, India_statewise)

if enable_GeoJSON_saving:
  India_statewise.to_file('India_statewise_minified.geojson', driver='GeoJSON')

India_stats = apply_corrections(India_stats)

if len(sars_cov2_data.columns) == 6:
  del sars_cov2_data['active_cases']

sars_cov2_data = apply_corrections(sars_cov2_data)

sars_cov2_data = pd.merge(India_stats, sars_cov2_data, on='state', how='left')
sars_cov2_data = sars_cov2_data.fillna(0)
sars_cov2_data_copy = sars_cov2_data.copy()

no_sars_cov2_list = list(set(list(India_statewise.state.values)) -set(list(sars_cov2_data.state)))
if verbose:
  print('A total of: {} states with no reports of SARS-CoV2 ...'.format(len(no_sars_cov2_list)))
  if len(no_sars_cov2_list)>=1:
    print('\nStates in India with no SARS-CoV2 reports:')
    for no_sars_cov2_state in no_sars_cov2_list:
      print(f'\n{no_sars_cov2_state} ...')

def sars_cov2_json(sars_cov2_df:'Pandas dataframe', geo_df:'Pandas dataframe', verbose:bool=False)->dict:
    merged_df = pd.merge(geo_df, sars_cov2_df, on='state', how='left')

    try:
      merged_df = merged_df.fillna(0)
    except Exception as e:
      e = getattr(e, 'message', repr(e))
      print(f'Failed removing NaN values in the merged dataframe due to: {e} ...')
      merged_df.fillna({'total_cases': 0}, inplace=True)
      merged_df.fillna({'deaths': 0}, inplace=True)
      merged_df.fillna({'discharged': 0}, inplace=True)

      if verbose:
        print('Consider updating GeoPandas library ...')
  
    merged_json = json.loads(merged_df.to_json())
    json_data = json.dumps(merged_json)
    return {'json_data': json_data, 'data_frame': merged_df}

merged_data = sars_cov2_json(
  sars_cov2_data, 
  India_statewise, 
  verbose=verbose
)

merged_json = merged_data['json_data']

def CustomPalette(palette_type:'Bokeh palette', enable_colorInverse:bool=True)->'Bokeh palette':
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

def css_formatter(font_pixel_size=15, line_height=110, in_css=None):
  css = f'font-size: {font_pixel_size}px; font-weight: "bold"; font-family: "{HTML_FONT}"; line-height: {line_height}%; '
  if in_css:
    return in_css + css
  return f'{css}'

def advanced_stats_tool_tip_formatter(font_pixel_size:int=12)->'HTML string':
  return f"""
             <div style='{css_formatter(font_pixel_size-1)}'>
             <strong>@state</strong><br>
             </div>
             <div style='{css_formatter(font_pixel_size)}'>
             Reported cases: <strong>@total_cases{HTML_INT_FORMATTER_STR}</strong><br>
             <hr>
             <strong>Forecasts: </strong><br>
             <p style="color:red; margin:0px 0; margin-bottom: 0.15em; margin-top: 0.15em">+1 day: <strong>@preds_cases{HTML_INT_FORMATTER_STR} (±@preds_cases_std{HTML_INT_FORMATTER_STR})</strong></p>
             <p style="color:green; margin:0px 0; margin-bottom: 0.15em; margin-top: 0.15em">+3 days: <strong>@preds_cases_3{HTML_INT_FORMATTER_STR} (±@preds_cases_3_std{HTML_INT_FORMATTER_STR})</strong></p>
             <p style="color:blue; margin:0px 0; margin-bottom: 0.15em; margin-top: 0.15em">+7 days: <strong>@preds_cases_7{HTML_INT_FORMATTER_STR} (±@preds_cases_7_std{HTML_INT_FORMATTER_STR})</strong></p>
             </div>
             <hr>
             <div style='{css_formatter(font_pixel_size-1)}'>
             Data updated on: <strong>{DATA_UPDATE_DATE}</strong><br>
             Forecasts updated on: <strong>{FORECASTS_UPDATE_DATE}</strong><br>
             Forecasts by: <a href="https://moad.computer"><strong>MOAD.Computer</strong></a> <br>
             </div>
          """

def performance_stats_hover_tool_formatter(font_pixel_size:int=12)->'HTML string':
  return f"""<div style='{css_formatter(font_pixel_size-1)}'>
             <strong>@state</strong> <br>
             </div>
             <hr>
             <div style='{css_formatter(font_pixel_size)}'>
             Mean Absolute Percentage Error <strong>(MAPE)</strong>
             <p style="color:red; margin:0px 0; margin-bottom: 0.15em; margin-top: 0.15em">+1 day: <strong>@MAPE{HTML_FLOAT_FORMATTER_STR}</strong></p>
             <p style="color:green; margin:0px 0; margin-bottom: 0.15em; margin-top: 0.15em">+3 days: <strong>@MAPE_3{HTML_FLOAT_FORMATTER_STR}</strong></p>
             <p style="color:blue; margin:0px 0; margin-bottom: 0.15em; margin-top: 0.15em">+7 days: <strong>@MAPE_7{HTML_FLOAT_FORMATTER_STR}</strong></p>
             </div>
             <hr>  
             <div style='{css_formatter(font_pixel_size-1)}'>
             Data updated on: <strong>{DATA_UPDATE_DATE}</strong><br>
             Forecasts updated on: <strong>{FORECASTS_UPDATE_DATE}</strong><br>
             Forecasts by: <a href="https://moad.computer"><strong>MOAD.Computer</strong></a> <br>
             </div>
         """

def simple_stats_hover_tool_formatter(font_pixel_size:int=12)->'HTML string':   
  return f"""<div style='{css_formatter(font_pixel_size+1)}'>
             <strong>@state</strong> <br>
             </div>
             <div style='{css_formatter(font_pixel_size)}'>
             Cases: <strong>@total_cases{HTML_INT_FORMATTER_STR}</strong><br>
             Deaths: <strong>@deaths{HTML_INT_FORMATTER_STR}</strong>
             </div>
             <hr>  
             <div style='{css_formatter(font_pixel_size-1)}'>
             Data updated on: <strong>{DATA_UPDATE_DATE}</strong><br>
             Data source: <a href="https://mohfw.gov.in"><strong>MoHFW.gov.in</strong></a> <br>
             </div>                                              
          """

def regionwise_forecast_performance_hover_tool_formatter(font_pixel_size:int=12)->'HTML string':
  return f"""<div style='{css_formatter(font_pixel_size+1)}'>
             Forecast performance for: <strong>@plot_index</strong> <br>
             <div>
             <p style="color:black; margin:0px 0; margin-bottom: 0.15em; margin-top: 0.15em">Reported cases: <strong>@y_cases{HTML_INT_FORMATTER_STR}</strong></p>
             <p style="color:red; margin:0px 0; margin-bottom: 0.15em; margin-top: 0.15em">Forecast a day ago: <strong>@y_preds{HTML_INT_FORMATTER_STR} (±@y_std{HTML_INT_FORMATTER_STR})</strong></p> 
             <p style="color:green; margin:0px 0; margin-bottom: 0.15em; margin-top: 0.15em">Forecast 3 days ago: <strong>@y_preds3{HTML_INT_FORMATTER_STR} (±@y_3std{HTML_INT_FORMATTER_STR})</strong></p>
             <p style="color:blue; margin:0px 0; margin-bottom: 0.15em; margin-top: 0.15em">Forecast 7 days ago: <strong>@y_preds7{HTML_INT_FORMATTER_STR} (±@y_7std{HTML_INT_FORMATTER_STR})</strong></p>
             </div>
             <hr>
             <div style='{css_formatter(font_pixel_size-1)}'>
             Data updated on: <strong>{DATA_UPDATE_DATE}</strong><br>
             Forecasts updated on: <strong>{FORECASTS_UPDATE_DATE}</strong><br>
             Forecasts by: <a href="https://moad.computer"><strong>MOAD.Computer</strong></a> <br>
             </div>
             <hr>
         """

def create_custom_hover_tool(
      enable_advanced_hover_tool:bool, 
      enable_simple_hover_tool:bool, 
      enable_performance_hover_tool:bool
)->'Bokeh hover tool':

  advanced_stats_hover = HoverTool(
    tooltips=advanced_stats_tool_tip_formatter(font_pixel_size=12)
  )
  performance_stats_hover = HoverTool(
    tooltips=performance_stats_hover_tool_formatter(font_pixel_size=12)
  )
  simple_stats_hover = HoverTool(
    tooltips=simple_stats_hover_tool_formatter(font_pixel_size=12)
  )
  standard_hover = HoverTool(
    tooltips=[
      ('State','@state'),
      ('Cases', '@total_cases'),
      #('Discharged/migrated', '@discharged'),
      ('Deaths', '@deaths')
    ]
  )
  
  if enable_performance_hover_tool:
    hover  = performance_stats_hover
  elif enable_advanced_hover_tool:
    hover = advanced_stats_hover
  elif enable_simple_hover_tool:
    hover  = simple_stats_hover
  else:
    hover = standard_hover
  
  return hover

def MapOverlayFormatter(map_overlay):
  if map_overlay:
    xmin = 7557500
    xmax = 10950000
    ymin = 875000
    ymax = 4825000
    
    return xmin, xmax, ymin, ymax

def geographic_overlay(
      plt, 
      geosourceJson=None,
      colorBar=None,
      colorMapper=None,
      colorMode='',
      hoverTool=None,
      mapOverlay=True,
      enableTapTool=False,
      enableToolbar=True
):
  if mapOverlay:
    wmts = WMTSTileSource(url="https://c.tile.openstreetmap.org/{Z}/{X}/{Y}.png")
    plt.add_tile(wmts)
    plt.xaxis.axis_label = 'longitude'
    plt.yaxis.axis_label = 'latitude'
  
  plt.xgrid.grid_line_color = None
  plt.ygrid.grid_line_color = None

  plt.axis.visible = False

  plt.patches(
    'xs',
    'ys', 
    source = geosourceJson, 
    fill_color = {'field' : colorMode, 
                  'transform' : colorMapper},
    line_color = 'purple', 
    line_width = 0.05, 
    fill_alpha = 0.05 if enableTapTool else 0.05,
    nonselection_alpha = 0.05,
    hover_fill_alpha=0.65
  )

  plt.add_layout(colorBar, 'right')

  plt.add_tools(hoverTool)

  if enableTapTool:
    plt.add_tools(TapTool())

  if enableToolbar:
    plt.toolbar.autohide = True

  if plt.title is not None:
    plt.title.text_font_size = '30pt'
  
  return plt

def union_territory_correction(
      plt,
      state=None,
      idx=None,  
      input_df=None,
      geosourceJson=None, 
      colorBar=None,
      colorMapper=None,
      colorMode=None,
      advanced_plotting=False,
      verbose=False
):

  xx, yy = np.array(India_statewise[India_statewise['state'] == state]['geometry'])[idx].exterior.coords.xy

  opt_list = []
  for i in ['total_cases',   'deaths',                        \
            'preds_cases',   'preds_cases_std',   'MAPE',     \
            'preds_cases_3', 'preds_cases_3_std', 'MAPE_3',   \
            'preds_cases_7', 'preds_cases_7_std', 'MAPE_7']:
    try:
      opt_val = input_df.loc[input_df['state']==state, i]
      opt_list.append([opt_val if len(opt_val) == 1 else list(opt_val)[0]])
    except Exception as e:
      if verbose:
        print(state, e, i)
      opt_list.append([0])

  if advanced_plotting:
    source = ColumnDataSource(

      data = dict(

        x=[np.mean(xx)],
        y=[np.mean(yy)],
        state=[state],
        total_cases=opt_list[0],
        deaths=opt_list[1],
        preds_cases=opt_list[2],
        preds_cases_std=opt_list[3],
        MAPE=opt_list[4],
        preds_cases_3=opt_list[5],
        preds_cases_3_std=opt_list[6],
        MAPE_3=opt_list[7],
        preds_cases_7=opt_list[8],
        preds_cases_7_std=opt_list[9],
        MAPE_7=opt_list[10]

      )

    )
  else:
    source = ColumnDataSource(

      data = dict(

        x=[np.mean(xx)],
        y=[np.mean(yy)],
        state=[state],
        total_cases=[input_df.loc[input_df['state']==state,'total_cases']],
        deaths=[input_df.loc[input_df['state']==state,'deaths']]

      )

    )

  if version_check:
    plot_circle = plt.scatter
  else:
    plot_circle = plt.circle

  plot_circle(

    x='x', 
    y='y', 
    size=25, 
    source=source,
    line_color='blue',
    line_width=0.25,  
    #color='blue',
    fill_alpha=0.05, 
    fill_color={'field'     : colorMode, 
                'transform' : colorMapper},  
    nonselection_alpha=0.1,
    hover_fill_alpha=0.15

  )

  return plt

def CustomTitleFormatter():

  xtext = 8350000
  ytext = 4425000
  xbox = 9400000
  ybox = 4575000

  return xtext, ytext, xbox, ybox

def CustomTitleOverlay(
      plt,  
      xtext=0,
      ytext=0,
      xbox=0, 
      ybox=0,
      input_df=None, 
      advanced_plotting=False
):
  
  overlay_text = Label(

    x=xtext, 
    y=ytext, 
    text='SARS-CoV2 in India',
    text_font=PLOT_FONT,
    text_font_size='21pt',
    text_font_style='bold'

  )
    
  plt.add_layout(overlay_text) 

  if advanced_plotting:
    print(sars_cov2_data['total_cases'].sum())  
    
    source = ColumnDataSource(

      data = dict(

        x=[xbox],
        y=[ybox],
        state=['India'],
        total_cases=[sars_cov2_data['total_cases'].sum()],
        deaths=[sars_cov2_data['deaths'].sum()],
        preds_cases=[preds_df['preds_cases'].sum()],
        preds_cases_std=[preds_df['preds_cases_std'].sum()],
        MAPE=[preds_df['MAPE'].mean()],
        preds_cases_3=[preds_df['preds_cases_3'].sum()],
        preds_cases_3_std=[preds_df['preds_cases_3_std'].sum()],
        MAPE_3=[preds_df['MAPE_3'].mean()],
        preds_cases_7=[preds_df['preds_cases_7'].sum()],
        preds_cases_7_std=[preds_df['preds_cases_7_std'].sum()],
        MAPE_7=[np.mean(np.abs(preds_df['MAPE_7']))]

      )

    )
  else:
    source = ColumnDataSource(
        data = dict(
                x=[xbox],
                y=[ybox],
                state=['India'],
                total_cases=[input_df['total_cases'].sum()],
                deaths=[input_df['deaths'].sum()]
              )
    )

  plt.rect(
    x='x', 
    y='y', 
    width=2250000, 
    height=250000, 
    color="#CAB2D6",
    source=source,
    line_color='purple',
    line_width=0.01,
    #width_units='screen',
    #height_units='screen',
    fill_alpha=0.1
  )  
  
  return plt

def sars_cov2_plot(
      sars_cov2_geosource,
      input_df=None,
      input_field=None,
      color_field='total_cases',
      plot_title=None,
      map_overlay=True,
      palette_type='OrRd',
      integer_plot=False,
      enable_simple_hover_tool=True,
      enable_union_territory_stats=True,
      enable_India_stats=False,                 
      enable_advanced_stats=False,
      enable_performance_stats=False,
      enable_foecast_perf=False,
      enable_toolbar=False
):
  
  palette = CustomPalette(
    palette_type, enable_colorInverse=False if enable_performance_stats else True
  )

  color_mapper = LinearColorMapper(
      palette=palette, 
      low=0, 
      high=int(10*(np.ceil(np.max(input_df[color_field].values)/10))) \
          if not enable_performance_stats else np.round((np.max(input_df[color_field].values)),3)
  )

  if integer_plot:
    format_tick = NumeralTickFormatter(format='0,0')
  else:
    format_tick = NumeralTickFormatter(
        format=str(input_df[input_field].values.astype('int')) if not enable_performance_stats else \
                str(np.round((input_df[input_field].values.astype('float')),1))
    )

  color_bar = ColorBar(
    color_mapper=color_mapper, 
    label_standoff=14, 
    formatter=format_tick,
    border_line_color=None, 
    major_label_text_font_size='12px',
    location = (0, 0),
    major_label_text_font=PLOT_FONT
  )

  xmin, xmax, ymin, ymax = MapOverlayFormatter(map_overlay)

  hover = create_custom_hover_tool(
    enable_advanced_stats, 
    enable_simple_hover_tool, 
    enable_performance_stats
  )

  plt = figure(
    title=plot_title,
    x_range=(xmin, xmax) if map_overlay else None,
    y_range=(ymin, ymax) if map_overlay else None,
    tools='save' if enable_toolbar else '', 
    outer_height = 512, outer_width = 512,
    toolbar_location = 'left' if enable_toolbar else None,
    lod_factor=int(1e7),
    lod_threshold=int(2),
    #output_backend="webgl"
  )
        
  plt = geographic_overlay(
    plt, 
    geosourceJson=sars_cov2_geosource,
    colorBar=color_bar,
    colorMapper=color_mapper,
    colorMode=input_field,
    hoverTool=hover,
    mapOverlay=map_overlay,
    enableToolbar=enable_toolbar,
    enableTapTool=True if ((enable_advanced_stats) or (enable_performance_stats)) else False
  )
  
  if enable_union_territory_stats:
    for i in range(8):
      plt = union_territory_correction(
        plt,
        state='Andaman and Nicobar Islands',
        idx=i,
        input_df=input_df,
        geosourceJson=sars_cov2_geosource,
        colorBar=color_bar, 
        colorMapper=color_mapper, 
        colorMode=input_field,
        advanced_plotting=True if ((enable_advanced_stats) or (enable_performance_stats)) else False
      )  

    plt = union_territory_correction(
      plt,
      state='Chandigarh',
      idx=0,
      input_df=input_df,
      geosourceJson=sars_cov2_geosource,
      colorBar=color_bar, 
      colorMapper=color_mapper, 
      colorMode=input_field,
      advanced_plotting=True if ((enable_advanced_stats) or (enable_performance_stats)) else False
    )

    for i in range(2):  
      plt = union_territory_correction(
        plt,
        state='Dadra and Nagar Haveli and Daman and Diu',
        idx=i,
        input_df=input_df,
        geosourceJson=sars_cov2_geosource,
        colorBar=color_bar, 
        colorMapper=color_mapper, 
        colorMode=input_field,
        advanced_plotting=True if ((enable_advanced_stats) or (enable_performance_stats)) else False
      )

    plt = union_territory_correction(
      plt,
      state='Delhi',
      idx=0,
      input_df=input_df,
      geosourceJson=sars_cov2_geosource,
      colorBar=color_bar, 
      colorMapper=color_mapper, 
      colorMode=input_field,
      advanced_plotting=True if ((enable_advanced_stats) or (enable_performance_stats)) else False
    )

    plt = union_territory_correction(
      plt,
      state='Chandigarh',
      idx=0,
      input_df=input_df,
      geosourceJson=sars_cov2_geosource,
      colorBar=color_bar, 
      colorMapper=color_mapper, 
      colorMode=input_field,
      advanced_plotting=True if ((enable_advanced_stats) or (enable_performance_stats)) else False
    )

    plt = union_territory_correction(
      plt,
      state='Lakshadweep',
      idx=0,
      input_df=input_df,
      geosourceJson=sars_cov2_geosource,
      colorBar=color_bar, 
      colorMapper=color_mapper, 
      colorMode=input_field,
      advanced_plotting=True if ((enable_advanced_stats) or (enable_performance_stats)) else False
    )

    for i in range(2):
      plt = union_territory_correction(
        plt,
        state='Puducherry',
        idx=i,
        input_df=input_df,
        geosourceJson=sars_cov2_geosource,
        colorBar=color_bar, 
        colorMapper=color_mapper, 
        colorMode=input_field,
        advanced_plotting=True if ((enable_advanced_stats) or (enable_performance_stats)) else False
      )

  if enable_India_stats:
    xtext, ytext, xbox, ybox = CustomTitleFormatter()

    plt = CustomTitleOverlay(
      plt, 
      xtext=xtext,
      ytext=ytext,
      xbox=xbox, 
      ybox=ybox,
      input_df=input_df,
      advanced_plotting=True if ((enable_advanced_stats) or (enable_performance_stats)) else False
    )

  plt.xaxis.axis_label_text_font  = PLOT_FONT
  plt.xaxis.major_label_text_font = PLOT_FONT
  plt.yaxis.major_label_text_font = PLOT_FONT

  plt.xaxis.major_tick_line_color = None  
  plt.yaxis.major_tick_line_color = None
  plt.xaxis.minor_tick_line_color = None 
  plt.yaxis.minor_tick_line_color = None

  plt.xaxis[0].ticker.num_minor_ticks = 0
  plt.yaxis[0].ticker.num_minor_ticks = 0

  plt.yaxis.formatter = NumeralTickFormatter(format='0,0')

  return plt

advanced_mode = True

sars_cov2_geosource = GeoJSONDataSource(geojson=merged_json)
sars_cov2_geosource = np.nan_to_num(sars_cov2_geosource, nan=0, posinf=0, neginf=0)
plot_title = None
app_title = 'India SARS-CoV2 statewise statistics'

india_total_cases = sars_cov2_data['total_cases'].sum()
india_total_deaths = sars_cov2_data['deaths'].sum()

if verbose:
  print(f'Total reported cases for {DATA_UPDATE_DATE}: {india_total_cases} ...')
  print(f'Total reported deaths for {DATA_UPDATE_DATE}: {india_total_deaths} ...')

def create_visualization_tabs(advanced_mode=True):
  tabs = []
  basic_sars_cov2_plot = sars_cov2_plot(
    sars_cov2_geosource, 
    input_df=sars_cov2_data,
    input_field='total_cases',
    color_field='total_cases',
    enable_India_stats=True,
    integer_plot=True,
    plot_title=plot_title
  )

  basic_plot_tab = Tab_Panel(
    child=basic_sars_cov2_plot, 
    title='⌂'
  )

  tabs.append(basic_plot_tab)

  if advanced_mode:
    preds_df.columns = ['state',                                                        \
                        'preds_cases_7', 'preds_cases_3', 'preds_cases',                \
                        'preds_cases_7_std', 'preds_cases_3_std', 'preds_cases_std',    \
                        'MAPE', 'MAPE_3', 'MAPE_7']

    if verbose:
      print(preds_df.head(10))
      print(sars_cov2_data_copy.head(10))

    preds_sars_cov2_df = pd.merge(
      sars_cov2_data_copy, 
      preds_df, 
      on='state', 
      how='left'
    )

    preds_sars_cov2_df = preds_sars_cov2_df.fillna(0)

    if verbose:
      print(preds_sars_cov2_df.head(10))
    
    try:
      del preds_sars_cov2_df['ID']
    except Exception as e:
      e = getattr(e, 'message', repr(e))
      if verbose:
        print(f'Unable to delete dataframe item: ID due to: {e} ...')

    try:
      del preds_sars_cov2_df['id']
    except Exception as e:
      e = getattr(e, 'message', repr(e))
      if verbose:
        print(f'Unable to delete dataframe item: id due to: {e} ...')

    try:
      del preds_sars_cov2_df['discharged']
    except Exception as e:
      e = getattr(e, 'message', repr(e))
      if verbose:
        print(f'Unable to delete dataframe item: discharged due to: {e} ...')

    merged_preds_data  = sars_cov2_json(
      preds_sars_cov2_df, 
      India_statewise
    )

    merged_preds_json  = merged_preds_data['json_data']
    preds_sars_cov2_data = merged_preds_data['data_frame']

    if verbose:
      print(preds_sars_cov2_data['state'].equals(sars_cov2_data['state']))
      print(set(list(preds_sars_cov2_data['state'])) - set(list(sars_cov2_data['state'])))

    preds_sars_cov2_geosource = GeoJSONDataSource(geojson=merged_preds_json)

    preds_sars_cov2_geosource= np.nan_to_num(
      preds_sars_cov2_geosource, 
      nan=0, 
      posinf=0, 
      neginf=0
    )

    preds_sars_cov2_data = preds_sars_cov2_data.fillna(0)

    advanced_sars_cov2_plot = sars_cov2_plot(
      preds_sars_cov2_geosource, 
      input_df=preds_sars_cov2_data,
      input_field='preds_cases_7',
      color_field='total_cases',
      enable_India_stats=True,
      enable_advanced_stats=True,
      integer_plot=True,
      plot_title=None
    )

    advanced_plot_tab = Tab_Panel(
      child=advanced_sars_cov2_plot, 
      title='Forecast'
    )

    tabs.append(advanced_plot_tab)

    performance_sars_cov2_plot = sars_cov2_plot(
      preds_sars_cov2_geosource, 
      input_df=preds_sars_cov2_data,
      palette_type='Greens',
      input_field='MAPE_7',
      color_field='MAPE_7',
      enable_India_stats=True,
      enable_performance_stats=True,
      plot_title=None
    )

    performance_plot_tab = Tab_Panel(
      child=performance_sars_cov2_plot, 
      title='Forecast quality'
    )

    tabs.append(performance_plot_tab)

  return tabs

def LineSmoothing(
      x, y, interpolationType='cubic', interpolationPoints=1000
):
  fn = interp1d(
    x, y, kind=interpolationType
  )

  x_lns = np.linspace(
    np.min(x), np.max(x), interpolationPoints
  )
  
  y_lns = fn(x_lns)

  return x_lns, y_lns

def model_performance_plot(
      source,
      use_cds=False,
      enable_interpolation=False, 
      regionwise_forecast_perf_hover_tool=True
):
    if use_cds:
      plotIndex = source.data['plot_index']
      plotIndex_labels = source.data['plot_labels']
      dateLabels = {i: date for i, date in enumerate(plotIndex_labels)}
      x=source.data['x']
    else:
      plotIndex_labels  = list(source['date'].astype('str'))  
      model_performance = source.fillna(0)  
      x = [i for i in range(len(list(source['date'].astype('str'))))]

      y_cases  = list(source['total_cases'].astype('int'))
      y_preds  = list(source['preds_cases'].astype('int'))
      y_preds3 = list(source['preds_cases_3'].astype('int'))
      y_preds7 = list(source['preds_cases_7'].astype('int'))

      y_stdev   = list(source['preds_cases_std'].astype('int'))
      y_3_stdev = list(source['preds_cases_3_std'].astype('int'))
      y_7_stdev = list(source['preds_cases_7_std'].astype('int'))

      lower_lim   = list(np.asarray(y_preds)-3*np.asarray(y_stdev))
      lower_3_lim = list(np.asarray(y_preds3)-3*np.asarray(y_3_stdev))
      lower_7_lim = list(np.asarray(y_preds7)-3*np.asarray(y_7_stdev))

      upper_lim   = list(np.asarray(y_preds)+3*np.asarray(y_stdev))
      upper_3_lim = list(np.asarray(y_preds3)+3*np.asarray(y_3_stdev))
      upper_7_lim = list(np.asarray(y_preds7)+3*np.asarray(y_7_stdev))

      plotIndex   = list(source['date'].astype('str'))
      dateLabels  = {i: date for i, date in enumerate(plotIndex)}

      source = ColumnDataSource(
        {
          'x':x,
          'plot_index':plotIndex,
          'plot_labels':plotIndex_labels, 
          'y_cases':y_cases,
          'y_preds':y_preds,
          'y_preds3':y_preds3,
          'y_preds7':y_preds7,
          'y_std':y_stdev,
          'y_3std':y_3_stdev,
          'y_7std':y_7_stdev,
          'upper_lim':upper_lim,
          'upper_3_lim':upper_3_lim,
          'upper_7_lim':upper_7_lim,
          'lower_lim':lower_lim,
          'lower_3_lim':lower_3_lim,
          'lower_7_lim':lower_7_lim
        }
      )
    
    if enable_interpolation:
      x_cases_interpol,y_cases_interpol   = LineSmoothing(x,y_cases)
      x_preds_interpol,y_preds_interpol   = LineSmoothing(x,y_preds)
      x_preds3_interpol,y_preds3_interpol = LineSmoothing(x,y_preds3) 
      x_preds7_interpol,y_preds7_interpol = LineSmoothing(x,y_preds7)

    if len(plotIndex)%2==0 or len(plotIndex)%5==0 or np.round((len(plotIndex)/10)/(len(plotIndex)//10))==1:
      for i in range(
                  len(plotIndex)//2
                    ):
        dateLabelObject = datetime.strptime(
          str(dateLabels[len(plotIndex)-1]),
          '%d-%B-%Y'
        )

        dateLabel_extra = dateLabelObject + timedelta(days=(i + 1))

        dateLabels.update(
          {len(plotIndex) + i : str(dateLabel_extra.strftime('%d-%B-%Y')) }
        )

    data_cases = dict(
      title=['report' for i in range(len(x))],
      plotIndex=plotIndex,
      x='x',
      y='y_cases',
      source=source
    )

    data_preds = dict(
      title=['forecast a day before' for i in range(len(x))],
      plotIndex='plot_index',
      x='x',
      y='y_preds',
      source=source
    )

    data_preds3 = dict(
      title=['forecast 3 days before' for i in range(len(x))],
      plotIndex='plot_index',
      x='x',
      y='y_preds3',
      source=source
    )

    data_preds7 = dict(
      title=['forecast 7 days before' for i in range(len(x))],
      plotIndex='plot_index',
      x='x',
      y='y_preds7',
      source=source
    )

    TOOLTIPS = regionwise_forecast_performance_hover_tool_formatter(
      font_pixel_size=12
    ) if regionwise_forecast_perf_hover_tool \
      else [('Date: ','@plot_index'), ('Cases: ','@y_cases')]

    perf_plot = figure(
      #y_axis_type="log",y_range=(2.5e4,7.5e4), 
      y_axis_location='left',
      outer_height=500, 
      outer_width=500,
      tools='hover', 
      toolbar_location=None,
      tooltips=TOOLTIPS
    )

    if version_check:
      perf_plot_circle = getattr(perf_plot, 'scatter')
    else:
      perf_plot_circle = getattr(perf_plot, 'circle')

    perf_plot.line(
      x='x',
      y='y_cases',
      source=source,
      line_width=2.5, 
      color='black'
    )

    r = perf_plot_circle(
      x='x', 
      y='y_cases', 
      color='grey', 
      fill_color='black',
      size=8, 
      source=source
    )

    perf_plot.line(
      x='x',
      y='y_preds',
      source=source,
      color='darkred'
    )

    r1 = perf_plot_circle(
      x='x', 
      y='y_preds', 
      color='darkred', 
      fill_color='red',
      size=8, 
      source=source
    )

    perf_plot.line(
      x='x',
      y='y_preds3',
      source=source,
      color='green'
    )

    r3 = perf_plot_circle(
      x='x', 
      y='y_preds3', 
      color='lime', 
      fill_color='darkgreen', 
      size=8,
      source=source
    )

    perf_plot.line(
      x='x',
      y='y_preds7', 
      source=source,
      color='blue'
    )

    r7 = perf_plot_circle(
      x='x', 
      y='y_preds7', 
      color='purple', 
      fill_color='blue', 
      size=8,
      source=source
    )

    perf_plot.hover.renderers = [r, r1, r3, r7]
    
    perf_plot.yaxis.formatter.use_scientific = False
    perf_plot.yaxis.formatter = NumeralTickFormatter(format='0,0')
    
    perf_plot.xaxis.major_label_overrides = dateLabels
    perf_plot.xaxis.axis_label = 'Date'
    perf_plot.yaxis.axis_label = ' '
    perf_plot.yaxis.axis_label_text_align = 'left'

    perf_plot.xaxis.axis_label_text_font  = PLOT_FONT
    perf_plot.xaxis.major_label_text_font = PLOT_FONT
    perf_plot.yaxis.major_label_text_font = PLOT_FONT

    perf_plot.add_layout(
      LinearAxis(
        axis_label='SARS-CoV2 cases',
        axis_label_text_font=PLOT_FONT,
        major_tick_line_color=None,
        minor_tick_line_color=None,
        major_label_text_font_size='0pt',
        major_label_orientation=math.pi,
      ), 
      'right'
    )

    perf_plot.right[0].axis_line_color = None
    perf_plot.right[0].formatter.use_scientific = False

    perf_plot.right[0].ticker.num_minor_ticks = 0
    perf_plot.yaxis.major_label_orientation   = (math.pi*.75)/2
    perf_plot.xaxis.major_label_orientation   = (math.pi*.75)/2

    band = Band(
      base='x',
      lower='lower_lim',
      upper='upper_lim',
      source=source, 
      level='underlay',
      fill_alpha=0.5,
      line_width=1,
      fill_color='indianred',
      line_color='indianred'
    )
  
    band3 = Band(
      base='x',
      lower='lower_3_lim',
      upper='upper_3_lim',
      source=source, 
      level='underlay',
      fill_alpha=0.4,
      line_width=1,
      fill_color='lime',
      line_color='lime'
    )
  
    band7 = Band(
      base='x',
      lower='lower_7_lim',
      upper='upper_7_lim',
      source=source, 
      level='underlay',
      fill_alpha=0.25,
      line_width=1,
      fill_color='indigo',
      line_color='indigo'
    )

    perf_plot.renderers.append(band)
    perf_plot.renderers.append(band3)
    perf_plot.renderers.append(band7)

    return perf_plot

def date_formatter(x):
  datetimeobject = datetime.strptime(str(x),'%Y%m%d')

  return datetimeobject.strftime('%d-%B-%Y')

def make_dataset(state):
  MODEL_PERF_DATA_SOURCE = f'{DATA_URL}{PERF_FILENAME_POINTER_STR}'
  MODEL_PERF_DATA_URL = '{}{}.csv'.format(MODEL_PERF_DATA_SOURCE, state)
  MODEL_PERF_DATA_URL = MODEL_PERF_DATA_URL.replace(' ', '%20')
  MODEL_PERF_DATA_FILE = os_style_formatter(
    f'{LOCAL_DATA_DIR}{PERF_FILENAME_POINTER_STR}{state}.csv'
  )

  try:
    model_performance = pd.read_csv(MODEL_PERF_DATA_URL)
    print(f'Reading model performance for: {state} from URL ...')
  except Exception as e:
    e = getattr(e, 'message', repr(e))
    print(f'Failed to read model performance data from URL due to: {e} ...')
    if os.path.exists(MODEL_PERF_DATA_FILE):
      model_performance = pd.read_csv(MODEL_PERF_DATA_FILE)  
      print(f'Reading model performance for: {state} from saved repo file: {MODEL_PERF_DATA_FILE} ...')
    else:
      sys.exit('No statewise model performance file found ...')

  model_performance['date'] = model_performance['date'].apply(lambda x: date_formatter(x))  
  plotIndex_labels = list(model_performance['date'].astype('str'))
  
  model_performance = model_performance.fillna(0)
  plotIndex = list(model_performance['date'].astype('str'))   
    
  x=[i for i in range(len(list(model_performance['date'].astype('str'))))]

  y_cases = list(model_performance['total_cases'].astype('int'))

  y_preds  = list(model_performance['preds_cases'].astype('int'))
  y_preds3 = list(model_performance['preds_cases_3'].astype('int'))
  y_preds7 = list(model_performance['preds_cases_7'].astype('int'))

  y_std  = list(model_performance['preds_cases_std'].astype('int'))
  y_3std = list(model_performance['preds_cases_3_std'].astype('int'))
  y_7std = list(model_performance['preds_cases_7_std'].astype('int'))
      
  lower_lim   = list(np.asarray(y_preds)-3*np.asarray(y_std))
  lower_3_lim = list(np.asarray(y_preds3)-3*np.asarray(y_3std))
  lower_7_lim = list(np.asarray(y_preds7)-3*np.asarray(y_7std))

  upper_lim   = list(np.asarray(y_preds)+3*np.asarray(y_std))
  upper_3_lim = list(np.asarray(y_preds3)+3*np.asarray(y_3std))
  upper_7_lim = list(np.asarray(y_preds7)+3*np.asarray(y_7std))

  return ColumnDataSource(
    {
      'x':x, 
      'y_cases':y_cases, 
      'plot_index': plotIndex, 
      'plot_labels':plotIndex_labels, 
      'y_preds':y_preds, 
      'y_preds3':y_preds3, 
      'y_preds7':y_preds7,
      'y_std':y_std, 
      'y_3std':y_3std,
      'y_7std':y_7std,
      'upper_lim':upper_lim,
      'upper_3_lim':upper_3_lim,
      'upper_7_lim':upper_7_lim,
      'lower_lim':lower_lim,
      'lower_3_lim':lower_3_lim,
      'lower_7_lim':lower_7_lim
    }
  )

class SARS_COV2_Layout():
  def __init__(
      self, 
      default_region_selection='India', 
      advanced_mode=False
    ):
    self.enable_source_creation=True
    self.default_region_selection=default_region_selection
    self.advanced_mode=advanced_mode
    self.model_performance=None
    self.state_list=sorted(list(preds_df['state']))
    self.state_list.append('India (Aggregate)')
    self.state_select=Select(
      value=self.default_region_selection,
      title='Select region or state: ', 
      options=self.state_list
    )
    self.place_holder='  '
    self.place_holder_str='p_str'
    self.state_wise_model_perf_dict=dict()
    self.state_wise_model_perf_data=[]

  def build_dataset(self):
    self.state_list.append(self.place_holder)
    for s_idx, s in enumerate(list(self.state_list)):
      if s == self.place_holder or s is None:
        self.state_wise_model_perf_dict.update({self.place_holder_str : s_idx})
        self.state_wise_model_perf_data.append([make_dataset(self.default_region_selection)])
      elif s == 'India (Aggregate)':
        self.state_wise_model_perf_dict.update({s : s_idx})
        self.state_wise_model_perf_dict.update({'India' : s_idx})
        self.state_wise_model_perf_data.append([make_dataset('India')])
      else:
        self.state_wise_model_perf_dict.update({s : s_idx})
        self.state_wise_model_perf_data.append([make_dataset(s)])

  def read_model_performance_data(self):
    if self.default_region_selection == self.place_holder and self.default_region_selection is not None:
      s = 'India'
    else:
      s = self.default_region_selection
    try:
      self.model_performance = pd.read_csv(
        f'{DATA_URL}{PERF_FILENAME_POINTER_STR}{s}.csv'
      )
    except Exception as e:
      e = getattr(e, 'message', repr(e))
      print(f'Failed to read model performance data for India from URL due to: {e} ...')

      India_model_performance_file = os_style_formatter(
        f'{LOCAL_DATA_DIR}{PERF_FILENAME_POINTER_STR}{s}.csv'
      )
      print(India_model_performance_file)
  
      if os.path.exists(India_model_performance_file):
        self.model_performance = pd.read_csv(India_model_performance_file)
        print(f'Reading India model performance file: {India_model_performance_file} from saved repo ...')
      else:
        print('Failed to read India model performance file: {India_model_performance_file} ...')

  def get_source(self):
    try:
      state_selection = self.state_select.value
    except NameError:
      state_selection = self.default_region_selection

    if state_selection is None:
      state_selection = self.default_region_selection

    if self.state_select.value == self.default_region_selection or self.state_select.value is None:
      state_idx = self.state_wise_model_perf_dict[self.place_holder_str]
    else:
      state_idx = self.state_wise_model_perf_dict[state_selection]

    if self.enable_source_creation:
      self.enable_source_creation = False
      global source
      source = self.state_wise_model_perf_data[state_idx][0]
    else:
      source.data.update(self.state_wise_model_perf_data[state_idx][0].data)

    return source

  def tab_switching_style_formatter(self, r=50, g=100, b=196):
    font_family      = f"font-family: '{HTML_FONT}'"
    hover_color      = f'background-color: rgba({r}, {g}, {b}, 0.35)' 
    bg_color         = f'background-color: rgba({r}, {g}, {b}, 0.10)'  
    select_bg_color  = f'background-color: rgba({r}, {g}, {b}, 0.01)'  
    bg_tab_color     = f'background-color: rgba({r}, {g}, {b}, 0.20)'   
    active_tab_color = f'background-color: rgba({r}, {g}, {b}, 0.32)'

    header_css  = '.bk-header {' + f'{bg_color};'  +                         \
                        'font-style: normal;                                 \
                         font-weight: normal;'  + font_family + '}'

    tab_css  = '.bk-tab {' + f'{bg_tab_color};'  +                           \
               'font-style: normal;                                          \
                border-radius: 2px;                                          \
                font-weight: normal;'  + font_family + '}'

    active_tab_css = '.bk-active.bk-tab {' + f'{active_tab_color};'  +      \
                     'font-style: normal;                                   \
                      font-weight: bold;'  + font_family + '}'

    hover_tab_css = ' .bk-tab:hover{' + hover_color + '}'

    column_css  = '.bk-Column {' + f'{select_bg_color};'  +                  \
                  'font-style: normal;                                       \
                   font-weight: normal;'  + font_family + '}'

    select_css  = '.bk-Select {' + f'{select_bg_color};'  +                  \
                  'font-style: normal;                                       \
                   font-weight: normal;'  + font_family + '}'

    input_group_css  = '.bk-input-group {' + f'{select_bg_color};'  +        \
                       'font-style: normal;                                  \
                        font-weight: normal;'  + font_family + '}'

    input_css  = '.bk-input {' + f'{select_bg_color};'  +                    \
                 'font-style: normal;                                        \
                  font-weight: normal;'  + font_family + '}'

    active_input_css  = '.bk-input:active {' + f'{select_bg_color};'  +      \
                        'font-style: normal;                                 \
                         font-weight: bold;'  + font_family + '}' 
                    
    css_style = str(
      '\n' + header_css +       \
      '\n' + tab_css +          \
      '\n' + active_tab_css+    \
      '\n' + hover_tab_css +    \
      '\n' + select_css +       \
      '\n' + input_group_css +  \
      '\n' + input_css +        \
      '\n' + active_input_css + \
      '\n' + column_css
    )

    return f"""<html><head><style, class='Tab Switching'> \
                {str(css_style)}                          \
              </style></head></html>                      \
           """

  def update_plot(self, attrname, old, new):
    new_source = self.get_source()
    source.data.update(new_source.data)

  def create_countrywide_model_performance_tab(self):
    self.read_model_performance_data()
    self.model_performance['date'] = self.model_performance['date'].apply(lambda x: date_formatter(x))
    model_perf_plot = model_performance_plot(self.model_performance)  
    model_performance_tab = Tab_Panel(
      child=model_perf_plot, 
      title='Countrywide forecast performance'
    )
    return model_performance_tab

  def create_statewise_model_performance_tab(self):
    statewise_plot = model_performance_plot(self.get_source(), use_cds=True)
    statewise_layout = Column_Layout(self.state_select, statewise_plot) 
    statewise_perf_tab = Tab_Panel(
      child=statewise_layout, 
      title='Regionwise forecast performance'
    )
    return statewise_perf_tab

  def create_sars_cov2_layout(self, default_region_selection='India'):
    if self.advanced_mode:
      self.default_region_selection = default_region_selection
      self.state_select.on_change('value', self.update_plot)
      self.build_dataset()
      statewise_perf_tab = self.create_statewise_model_performance_tab()
      countrywide_perf_tab = self.create_countrywide_model_performance_tab()
      viz_tabs = create_visualization_tabs(advanced_mode=advanced_mode)
      viz_tabs.extend([countrywide_perf_tab, statewise_perf_tab])
      sars_cov2_layout_tabs = Tabs(tabs=viz_tabs)
      sars_cov2_layout_tabs.stylesheets.append(self.tab_switching_style_formatter())
      sars_cov2_layout = sars_cov2_layout_tabs
      return sars_cov2_layout, self.state_select
    else:
      sars_cov2_layout = Column_Layout(basic_sars_cov2_plot)
      return sars_cov2_layout, None

curdoc().title = app_title

if __name__ == '__main__':
  out_file('India_SARS_CoV2.html')
  viz_tabs = create_visualization_tabs(advanced_mode=advanced_mode)
  plot_layout = SARS_COV2_Layout(advanced_mode=advanced_mode)
  perf_tab = plot_layout.create_countrywide_model_performance_tab()
  viz_tabs.append(perf_tab)
  plot_tab = Tabs(tabs=viz_tabs)
  plot_tab.stylesheets.append(plot_layout.tab_switching_style_formatter())
  save(
    plot_tab, 
    title='India SARS-CoV2 statewise statistics'
  )
else:
  sars_cov2_layout, _ = SARS_COV2_Layout(
    default_region_selection='India', 
    advanced_mode=advanced_mode
  ).create_sars_cov2_layout()
  curdoc().add_root(sars_cov2_layout)