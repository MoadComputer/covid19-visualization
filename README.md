# covid19-visualization
Visualization tool for COVID19 outbreak in India using GeoPandas and Bokeh

## **App deployment**

### 1. [Jupyter notebook](https://github.com/MoadComputer/covid19-visualization/blob/main/examples/COVID19_India.ipynb) or [Google Colab](https://colab.research.google.com/github/MoadComputer/covid19-visualization/blob/main/examples/COVID19_India.ipynb)

  **For Jupyter/JupyterHub/JupyterLab in AMD64/x86-64 Linux machines** 
    
  * Run the notebook by selecting from the menu: ```Kernel``` and  then: ```Restart & Run All```
  [![Jupyter how-to](https://github.com/MoadComputer/covid19-visualization/raw/main/examples/Jupyer_howto.png)](https://github.com/MoadComputer/covid19-visualization/blob/main/examples/COVID19_India.ipynb)

  **For Jupyter in AARCH64 Linux machines**
    
  * Deploy Bokeh server for AARCH64 Linux using the cheatsheet below
  * Edit the first cell to: ```setup=False```
  * Run the notebook

  **For Jupyter in Windows machines**
   
  * Deploy Bokeh server using the cheatsheet below
  * Activate conda virtualenv: ```conda activate GeoPandas```
  * Install Jupyter and ipykernel: ```conda install -c conda-forge python=3 notebook ipykernel --yes```
  * Run Jupyter: ```jupyter notebook```
  * Edit the first cell to: ```setup=False```
  * Run the notebook

  **For Google Colab**
    
  * Launch using the Google Colab link, go to: ```Runtime```, select: ```Run all``` or press ```CTRL+F9```
  * Accept the Google Colab warning about notebook not authored by Google by clicking: ```Run anyway```
  [![Google Colab how-to](https://github.com/MoadComputer/covid19-visualization/raw/main/examples/Google_Colab_howto.png)](https://colab.research.google.com/github/MoadComputer/covid19-visualization/blob/main/examples/COVID19_India.ipynb)

### 2. Bokeh server app

* Git clone the repositroy: ```git clone https://github.com/MoadComputer/covid19-visualization; cd covid19-visualization```
* Launch the Bokeh server: ```bokeh serve --show ./app/COVID19_India.py```
* Go to your browser location and the app will be served
  [![Bokeh static output](https://github.com/MoadComputer/covid19-visualization/raw/main/examples/COVID19_India_Bokeh_output.png)](https://www.moad.computer/blog/covid19-outbreak-visualized-using-python)

## **Bokeh server deployment cheatsheet**

**For AMD64/x86-64 Linux users**

* Install git: ```apt install git```
* Clone the repo: ```git clone git clone https://github.com/MoadComputer/covid19-visualization; cd covid19-visualization```
* Use the requirements file to install dependencies: ```python3 -m pip install -r ./requirements.txt```

**For AARCH64 Linux users**

* Install build tools and CMake: ```apt install make clang llvm libc++-dev libc++abi-dev```
* Install ```llmvmlite``` for python3: ```python3 -m pip install llvmlite```
* Install ```libatlas-dev```: ```apt install libatlas-base-dev```
* Install AARCH64 linux dependencies: ```apt install libgdal-dev gdal-bin python3-gdal libtiff-dev  libsqlite3-dev sqlite```
* Clone and prepare PROJ repository for CMake: ```git clone https://github.com/OSGeo/PROJ; cd ./PROJ; ./autogen```
* Configure PROJ: ```./configure```
* Make and install PROJ: ```make; make install```
* Install pyproj: ```python3 -m pip install git+https://github.com/pyproj4/pyproj.git```
* Install pandas: ```apt install python3-pandas```
* Install app dependencies: ```python3 -m pip install fiona geopandas shapely bokeh --no-deps```
* Install ```visvalingamwyatt``` for GeoJSON minification: ```python3 -m pip install visvalingamwyatt```

**For Windows users (Using [Anaconda Python3](https://repo.anaconda.com/archive/Anaconda3-2023.07-2-Windows-x86_64.exe))**

* Update conda: ```conda update -n base -c defaults conda```
* Create virtual Anaconda3 environment: ```conda create -n GeoPandas -c conda-forge python=3.11.5 geopandas --yes```
* Activate virtual Anaconda3 environment: ```conda env activate GeoPandas```
* Install git: ```conda install -n GeoPandas -c anaconda git```
* Install bokeh: ```conda install -n GeoPandas -c bokeh bokeh```
* Install matplolib: ```conda install -n GeoPandas -c conda-forge matplotlib descartes```
* Update nbformat: ```conda update nbformat```
* Install ```visvalingamwyatt``` for GeoJSON minification: ```python -m pip install visvalingamwyatt```
* To remove the application: deactivate the virtual environment ```conda deactivate GeoPandas``` and run ```conda env remove --name GeoPandas```