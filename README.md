# covid19-visualization
Visualization tool for COVID19 outbreak using GeoPandas and Bokeh

App deployment:

1. [Jupyter notebook](https://github.com/MoadComputer/covid19-visualization/blob/master/examples/COVID19_India.ipynb) or [Google Colab](https://colab.research.google.com/github/MoadComputer/covid19-visualization/blob/master/examples/COVID19_India.ipynb)

2. Web application [(eg. using Heroku)](https://covid19india-visualization.herokuapp.com/COVID19_India)

3. Bokeh server app
    * Git clone the repositroy: ```git clone https://github.com/MoadComputer/covid19-visualization; cd covid19-visualization```
    * Launch the Bokeh server: ```bokeh serve --show ./app/COVID19_India.py```
    * Go to your browser location and the app will be served
    ![Bokeh static output](https://github.com/MoadComputer/covid19-visualization/raw/master/examples/COVID19_India_Bokeh_output.png)

** Bokeh server deployment cheatsheet***
* For AMD64/x86-64 Linux users:
    * Install git: '''apt install git'''
    * Clone the repo: '''git clone git clone https://github.com/MoadComputer/covid19-visualization; cd covid19-visualization'''
    * Use the requirements file to install dependencies: '''python3 -m pip install -r ./requirements.txt'''
* For AARCH64 Linux user:
    * Install build tools and CMake: '''apt-get install make clang llvm libc++-dev libc++abi-dev'''
    * Install '''llmvmlite''' for python3: '''python3 -m pip install llvmlite'''
    * Install '''libatlas-dev''': '''apt-get install libatlas-base-dev'''
    * Install AARCH64 linux dependencies: '''apt install libgdal-dev gdal-bin python3-gdal libtiff-dev  libsqlite3-dev sqlite'''
    * Clone and prepare PROJ repository for CMake: '''git clone https://github.com/OSGeo/PROJ; cd ./PROJ; ./autogen'''
    * Configure PROJ: '''./configure'''
    * Make and install PROJ: '''make; make install'''
    * Install pyproj: '''python3 -m pip install git+https://github.com/pyproj4/pyproj.git'''
    * Install pandas: '''apt install python3-pandas'''
    * Install app dependecies: '''python3 -m pip install fiona geopandas shapely bokeh --no-deps'''
* For Windows users (Require [Anaconda Python3](https://repo.anaconda.com/archive/Anaconda3-2020.02-Windows-x86_64.exe)):
    * Create virtual Anaconda3 environment: '''conda env create --name GeoPandas python'''
    * Activate virtual Anaconda3 environment: '''conda env activate GeoPandas'''
    * [Install GeoPandas using conda forge](https://geopandas.org/install.html): '''conda install --channel conda-forge geopandas'''
    * [Download, unzip and extract libspatialindex dlls](http://download.osgeo.org/libspatialindex/libspatialindex-1.8.0-win-msvc-2010-x64-x32.zip) to: '''C:\ProgramData\Anaconda3\envs\GeoPandas'''
    * Install git: '''conda install -c anaconda git'''