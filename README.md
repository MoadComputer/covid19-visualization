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
