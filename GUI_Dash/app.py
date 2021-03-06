#! /usr/local/bin/python3

# lsof -i tcp:8050
#----------------------------------------------------------------------------------#
#WSGI Imports
import plotly
import webbrowser
from flask import Flask
from threading import Timer

#----------------------------------------------------------------------------------#
#Library Imports
import os, io, pickle, pathlib, statistics;
import pandas as pd
import plotly.io as pio
import plotly.express as px
import plotly.graph_objects as go
#----------------------------------------------------------------------------------#
#Dash Imports
import dash, base64, datetime;
#import dash_table
import dash_daq as daq
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
#----------------------------------------------------------------------------------#
# In-Built Api Imports
from loadPullDataAnalysis import mdfParser
from loadPullDataAnalysis import dataXformation as dx
#----------------------------------------------------------------------------------#
'''
Requirements: 
Plotly
flask
pandas
plotly.express
plotly.graph_objects
dash
dash_core_components 
dash_html_components
dash_bootstrap_components
dash.dependencies : Input, Output, State
'''
#-------------------------------------*Start App*------------------------------------------------#
#Start App
server = Flask(__name__)
app = dash.Dash(
	__name__,
	server=server,
	url_base_pathname='/LoadPull-Dashboard/',
	external_stylesheets=[dbc.themes.SUPERHERO]
	)

#-----------------------------------*API Function*-----------------------------------------------#
# Initiate global varibales that cover the scope of the entire code

global decoded, listOfDf, PICKLE_LOC, fileCheck, parsedDf, slider_range, slct, harm, slicedDfAtVarX
listOfDf = []
UPLOAD_DIRECTORY = "./app_uploaded_files"
PICKLE_LOC = None
df=pd.DataFrame()
parsedDf = pd.DataFrame()

#Create local file storage "app_uploaded_files"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True, mode=0o777)
os.chmod(UPLOAD_DIRECTORY, mode=0o777)
#-------------------------------------*List of dropdown*-----------------------------------------#

harm_list = ["1","2","3"]

splice_option_list = ["PAE", "Pout", "Gain"] # 

plot_option_list = ["PAE", "Gain", "gammaTuple", "Pout"]




#--------------------------------------App Layout------------------------------------------------#
app.layout = html.Div(className="d-flex flex-column", id='dash-container', children=[

	

	html.Header(className="page-header", children = [		

		html.Img(src=app.get_asset_url("logo192.png"), style={
															'float': 'left',
															'top':'10px',
															'left':'30px',
															'width': '90px',
															'position': 'relative'
														}),								
		html.Div([
		    html.H1("LoadPull Analysis Dashboard", 
		    		style={ 'margin-top':'10px', 'margin-left':'160px', 'font-size':'60px'})
		    ])
		]),
	html.Br(),

	html.Div(id = 'body', className="container-fluid flex-fill", children = [
		

			html.Div(className = "jumbotron",children = [
				html.H1("Welcome!", className="display-3",),
				html.P("This is a dashboard app to enable slicing and visualization Transistor Loadpull Data upon input of an MDF File Type.", className="lead"),
				html.Hr(className="my-4"),
				html.H5("This dashboard posseses 3 major functionalities: "),
				html.Ol(
					[
						html.Li("It uses api function calls to parse the mdf file input by our own in-built parse."),
						html.Li("Our parsed DataFrame is then fed through Dashboard used by the user to filter the DataFrame."),
						html.Li("The sliced and filtered DataFrame is used to render 3d plot using a python package, Plotly.")
					]),
				html.Div(className="lead" , children = [
					html.A("Read Documentation", className="btn btn-primary btn-lg", href="assets/index.html", target="_blank", role="button", style={"padding":"5px", "border-style":"dotted", "border-color":"black", "font-size":"15px"}),
					html.A("Explore GitHub Repo", className="btn btn-primary btn-lg", href="https://github.com/0xrutvij/loadPullDataAnalysis/blob/main/loadpulldataanalysis.pdf", target="_blank", role="button", style={"padding":"5px", "border-style":"dotted", "border-color":"black", "font-size":"15px"}),
					])
				]),

			html.Div(
				[
					dcc.Upload( id='upload-data', className='btn btn-outline-info',
								children=html.Div(["Drag and drop or click to select a file to upload."]),
					
            		style = {
            			"width": "100%",
		                "height": "60px",
		                "lineHeight": "40px",
		                "borderWidth": "2px",
		                "borderStyle": "dashed",
		                "borderRadius": "5px",
		                "textAlign": "center",
		                #"padding": "20px"
		                #"margin": "10px",
            		})
            	], 
            	style = {"padding":"10px"}

            ),
			html.H5(id="output-data-upload" , style = {"width":"100%", "align":"center"}),
				#
			
		
			html.Hr(style={
				            'borderStyle': 'dashed',
				            'width': '5px',
				            'color': 'white'
				        }),

			html.Br(),
			html.Br(),
			html.H2("Slicing/Plotting Selectors: "),
		    html.Div(id="dropdown-div", children=[
				
		    	dbc.Row(id="dropdown-row", children=[
				
		    		dbc.Col(children=[
						html.Label(['Select harmonic'], style={'font-weight': 'bold', "text-align": "left"}),
		    			dcc.Dropdown(id="slct_harm", options=[{'label':x, 'value':x}for x in harm_list], 
						style={'width':'150px','vertical-align':"middle", 'color': 'black'},
						value='1',
						multi=False, 
		    			), html.Span(id='harm_message', className='badge badge-success'),
					]),
		    		dbc.Col(children=[
						html.Label(['Select Slice'], style={'font-weight': 'bold', "text-align": "left"}),
		    			dcc.Dropdown(id="slct_splice", options=[{'label':x, 'value':x}for x in splice_option_list],
						style={'width':'250px','vertical-align':"middle", 'color': 'black'},
						placeholder = 'None',
						), 
						html.Span(id='splicing_message', className='badge badge-success'),
					]),
		    		dbc.Col(children=[
						html.Label(['Select Plotting Variable'], style={'font-weight': 'bold', "text-align": "left"}),
		    			dcc.Dropdown(id="slct_plot",options=[{'label':x, 'value':x}for x in plot_option_list],
						style={'width':'250px','vertical-align':"middle", 'color': 'black'},
						placeholder='None',
						), html.Span(id='plot_message', className='badge badge-success')
					])
				])
				
			], style={"display": "flex", "flexWrap": "wrap", "position":"relative"} ),

		    html.Div([
			    html.Br(),
			    html.Br(),
				html.Br(),
			]),
  
            html.Div([
            	dbc.Row([

					dbc.Col([html.H6(id='slider-label')],style={"width":"420px", "padding":"10px"}),
            		
					dbc.Col([
						daq.Slider(
	                    id="slice",
	                    size=500,
	                    #value=5, #default value
	                    handleLabel={"showCurrentValue": True,"label": "VALUE"},
	            		)], style={"padding-top":"20px"}
	            	)
	                 
            	], style={"padding-top":"20px", 'style':'800px'}),
            	dbc.Row([
            		dbc.Col([
            			dcc.Checklist(id='gComp-checklist',options=[
            				{'label' : ' gComp', 'value' : 'gComp'},
            			], value=[], style={'width': '150px', "padding-top":"15px"}, persistence=False, persistence_type='session')
            		]),
            		dbc.Col([html.H6(id='slider-label-2')],style={"width":"500px", 'text-align':'left', 'left':'-250px'}),
            		
					dbc.Col([
						daq.Slider(
	                    id="g-comp",
	                    min=0,
	                    max=10,
	                    step=1,
	                    size=300,
	                    #value=5, #default value
	                    handleLabel={"showCurrentValue": True,"label": "VALUE"},
	            		)], style={"padding-top":"15px", 'left':'-250px'}
	            	)
            	], style={"padding-top":"20px"})
            	
       		], style={"display": "flex", "flexWrap": "wrap", "padding-top":"20px"} ),
    	
		    html.Div(id='slider-output'),
			
			html.Div([
				dbc.Row([
					dbc.Col([html.Button('Plot Scatter', id='btn-nclicks-1', className = "btn btn-primary", type="button", style={"width":"100px"})]),
					dbc.Col([html.Button('Plot Contour', id='btn-nclicks-2', className = "btn btn-primary", type="button", style={"width":"100px"}),]),
					dbc.Col([html.Button('Plot Surface', id='btn-nclicks-3', className = "btn btn-primary", type="button", style={"width":"100px"}),]),
					dbc.Col([html.Button('Execute gComp Slice on data', id='btn-nclicks-4', className = "btn btn-primary", type="button", style={"width":"150px"}),]),
					])
            ], style={"display": "flex", "flexWrap": "wrap", "padding":"15px", "align":"center"}),
		    
		    dcc.Graph(id='plt', figure={}, style={'width':'700px', 'height':'700px'}) #set proper ID
		]),

		html.Footer() 
])

#----------------------------------------------------------------------------------#

#Callback Functioins 
def stale(filename):
	return dbc.Alert(id='stale',
            children=[html.B("Input a File!")],
            className="alert alert-dismissible alert-light",
            dismissable=False,
            is_open=True,
			)
def success(filename):
	return dbc.Alert(id='succ',
            children=[html.B("Success! File: \"{}\"  has been read.".format(filename))],
            className="alert alert-dismissible alert-success",
            dismissable=True,
            is_open=True,
			)
def fail(filename):
	return dbc.Alert(id='fail', 
            children=[html.B("Error Occurred! \"{}\"  is not valid file type".format(filename))],
            className="alert alert-dismissible alert-danger",
            dismissable=True,
            is_open=True,
			)


#Callback for file upload
@app.callback(

	Output(component_id='output-data-upload', component_property='children'),
	[Input(component_id='upload-data', component_property='contents'),
	Input(component_id='upload-data', component_property='filename')],
    )

def update_output(contents, names):
	global fileCheck
	children = True
	fileCheck = False
	if contents is not None:
		children = file_check(contents, names)
		fileCheck = True 
		#print(children)
		
		if children == True:
			output_data_upload = success(names)	
		elif children == False:
			output_data_upload = fail(names)
		elif children == 0:
			output_data_upload = stale(names)
				
	else:
		output_data_upload = stale(names)
	
	return output_data_upload


def uploaded_files():
    """List the files in the upload directory."""
    files = []
    for filename in os.listdir(UPLOAD_DIRECTORY):
        path = os.path.join(UPLOAD_DIRECTORY, filename)
        if os.path.isfile(path):
            files.append(filename)
    return files


#Filename parse function to check name
def file_check(contents, filename):

	filename = str(filename)
	global PICKLE_LOC

	try:
		if '.mdf' in str(filename):
			save_file(contents, filename)
			mdfLoc = str(UPLOAD_DIRECTORY+ "/" +filename)
			df = mdfParser.parseMdf(mdfLoc)
			df = mdfParser.calculateMetrics(df)
			df = mdfParser.unitConversions(df)
			

			filepath = UPLOAD_DIRECTORY + "/" + filename[:-4]
			PICKLE_LOC = filepath + '.pkl'
			mdfParser.exportFiles(df, filepath)
			print("Read and converted: ", filename)

			return True
		else:
			return False
		
	except ValueError:
		return False

	return 0

def save_file(content, name):
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode("utf8").split(b";base64,")[1]
    with open(os.path.join(UPLOAD_DIRECTORY, name), "wb") as fp:
        fp.write(base64.decodebytes(data))
#----------------------------------------------------------------------------------#

#Callback for harm slice
@app.callback(
	[
	Output(component_id='harm_message', component_property='children'),
	Output(component_id='splicing_message', component_property='children'),
	Output(component_id='plot_message', component_property='children'),
	
	],
	[
	Input(component_id='slct_harm', component_property='value'),
	Input(component_id='slct_splice', component_property='value'),
	Input(component_id='slct_plot', component_property='value'),
	
	]
	)

def drpdowns(slct_harm, slct_splice, slct_plot):
	
	
	global slct, PICKLE_LOC, harm
	# function call to slive df
	#sliceDF(slct_harm, slct_splice, slct_plot)
	#varInfoDict = getVarRangeForSlice(harm_message, splicing_message)

	if slct_splice and PICKLE_LOC is not None:
		
		splicing_message = "Slice option chosen:  {}".format(slct_splice)
		#slct = slct_splice
		
		#print(slider_range)
	else:
		splicing_message = "Slice option chosen:  {}".format("None")

	harm_message = "Harmonic set to:  {}".format(slct_harm)
	harm = slct_harm
	
	plot_message = "Plotting variable chosen:  {}".format(slct_plot)


	return harm_message, splicing_message, plot_message 

#----------------------------------------------------------------------------------#

@app.callback(
	[
	Output(component_id='slice', component_property='min'),
	Output(component_id='slice', component_property='max'),
	Output(component_id='slice', component_property='step'),
	#Output(component_id='slice', component_property='value'),

	#Output(component_id='slider-output', component_property='children'),
	Output(component_id='slider-label', component_property='children'),
	Output(component_id='slider-label-2', component_property='children')
	],

	[
	Input(component_id='slct_splice', component_property='value'),
	Input(component_id='slice', component_property='value'),
	Input(component_id='gComp-checklist', component_property='value'),
	Input(component_id='g-comp', component_property='value')
	]

	)
def slide(slct, slice, chk_gComp, g_comp):
	global PICKLE_LOC, fileCheck, harm
	min = 0
	max = 100
	step = 1
	value = 0
	n = 0


	if fileCheck is True:
		if slct is not None:
			min, max, step, value = getVarRangeForSlice(harm, slct)
			#slider_output = "Slider Value chosen:  {}".format(slice)
			n = 1
			slider_label = checkDrpDown(slct, n)
		else:
			
			#slider_output = "Slider Value chosen:  {}".format("0")
			n = 1
			slider_label = checkDrpDown(slct, n)
			
			pass
		if chk_gComp is not None:
			n = 2
			slider_label_2 = check_gComp(chk_gComp, slct, n)

		else:
			n= 2
			slider_label_2 = check_gComp(None, slct, n)
		
	else:
		n=1
		slider_label = checkDrpDown(slct, n)
		n=2
		slider_label_2 = check_gComp(chk_gComp, slct, n)
		
	
	return min, max, step, slider_label, slider_label_2 #slider_output,

def getVarRangeForSlice(harm, slice):
	global parsedDf, listOfDf, PICKLE_LOC
	if PICKLE_LOC:
		parsedDf = pd.read_pickle(PICKLE_LOC)
		parsedDf = dx.filterColVal(parsedDf, 'harmonic', 1, 'eq')
		parsedDf = dx.dfWithCols(parsedDf, ['gammaTuple', 'power', 'harmonic', 'Pin', 'Pout', 'Gain', 'PAE', 'drainEff',
        'r', 'jx'])
		parsedDf = dx.splitGammaTuple(parsedDf)
		listGamDf = dx.splitOnUniqueGammaTuples(parsedDf)

		for i,x in enumerate(listGamDf):
				listGamDf[i] =  dx.calcGComp(x)

		df = parsedDf
		listOfDf = listGamDf
		
		varInfoDict = dx.pickVariable(slice, parsedDf)

		maxV = varInfoDict['maxVal'] 
		minV = varInfoDict['minVal']
		step = varInfoDict['stepSize']
		defaultV = varInfoDict['defaultVal']
		return minV, maxV, step, defaultV

	else:
		return 0

def check_gComp(opt, slct, ind):
	global fileCheck
	if "gComp" in opt:
		if fileCheck is False:
			return dbc.Alert( 
		        children=[html.B("Please Choose a MDF File Input First!")],
		        className="alert alert-dismissible alert-warning",
		        dismissable=False,
		        is_open=True,
				)

		else:
			if slct is None:
				return dbc.Alert( 
		            children=[html.B("Please Choose a Slicing Slector!")],
		            className="alert alert-dismissible alert-danger",
		            dismissable=False,
		            is_open=True,
					)
			return dbc.Alert(
	            children=[html.B("Choose G Compression Selector ".format(opt))],
	            className="alert alert-dismissible alert-success",
	            dismissable=False,
	            is_open=True,
				)

	else:
		return dbc.Alert( 
	            children=[html.B("<< Enable G Compression Slice")],
	            className="alert alert-dismissible alert-danger",
	            dismissable=False,
	            is_open=True,
				)


def checkDrpDown(opt, ind):
	global fileCheck

	
	if opt is not None:
		if fileCheck is False:
			return dbc.Alert( 
		        children=[html.B("Please Choose a MDF File Input First!")],
		        className="alert alert-dismissible alert-warning",
		        dismissable=False,
		        is_open=True,
				)


		return dbc.Alert(
            children=[html.B("Choose slicing value for:			\"{}\" ".format(opt))],
            className="alert alert-dismissible alert-success",
            dismissable=False,
            is_open=True,
			)
	
	else:
		
		return dbc.Alert( 
	            children=[html.B("Please assign Slicing/Plotting Selectors ^^")],
	            className="alert alert-dismissible alert-danger",
	            dismissable=False,
	            is_open=True,
				)
#----------------------------------------------------------------------------------#

@app.callback(
	[Output(component_id='plt', component_property='figure')],
	[
	Input(component_id='btn-nclicks-1', component_property='n_clicks'),
	Input(component_id='btn-nclicks-2', component_property='n_clicks'),
	Input(component_id='btn-nclicks-3', component_property='n_clicks'),
	Input(component_id='btn-nclicks-4', component_property='n_clicks'),
	Input(component_id='slct_splice', component_property='value'),
	Input(component_id='slct_plot', component_property='value'),
	Input(component_id='slice', component_property='value'),
	Input(component_id='g-comp', component_property='value')]
	)

def graphing(btn_1, btn_2, btn_3, btn_4, sliceVar, slicePlot, sliceVal, g_comp):
	global fileCheck


	changed_id_1 = [p['prop_id'] for p in dash.callback_context.triggered][0]
	
	if 'btn-nclicks-1' in changed_id_1:
		return scatterPlot(sliceVar, sliceVal, slicePlot, g_comp)

	elif 'btn-nclicks-2' in changed_id_1:
		return contourPlot(sliceVar, sliceVal, slicePlot, g_comp)

	elif 'btn-nclicks-3' in changed_id_1:
		return surfacePlot(sliceVar, sliceVal, slicePlot, g_comp)
		
	elif 'btn-nclicks-4' in changed_id_1:
		return gCompFilter(sliceVar, sliceVal, slicePlot, g_comp)
	else:
		return [{}]

def scatterPlot(sliceVar, sliceVal, slicePlot, g_comp):
	global parsedDf, listOfDf 
	if fileCheck is True:
		selList, slicedDfAtVarX = dx.interpolatedSlice(listOfDf, sliceVar, sliceVal)
		#print(slicedDfAtVarX.head())
		#fig = go.Figure()
		
		fig = px.scatter(slicedDfAtVarX, x="r", y="jx", color=slicePlot, height=700, width=700) # color='PAE' , color=slicePlot, height=600, width=600
		#fig.update_layout(legend_font_color=slicedDfAtVarX[slicePlot])
		#fig.add_traces(px.scatter(data_frame=slicedDfAtVarX, x="r", y="jx",  height=700, width=700))
		return [fig]
		#dcc.Graph(figure=fig.show())
	else:
		return [{}]

def contourPlot(sliceVar, sliceVal, slicePlot, g_comp):
	global parsedDf, listOfDf 

	if fileCheck is True:
		selList, slicedDfAtVarX = dx.interpolatedSlice(listOfDf, sliceVar, sliceVal)
	
		fig = go.Figure(data =
		go.Contour(
			z= slicedDfAtVarX[slicePlot],
			x= slicedDfAtVarX['r'], # horizontal axis
			y= slicedDfAtVarX['jx'], # vertical axis
			line_smoothing=1.3
		))

		fig.update_layout(height=700, width=700)
		return [fig]
	else:
		return [{}]

def surfacePlot(sliceVar, sliceVal, slicePlot, g_comp):
	global parsedDf, listOfDf 

	if fileCheck is True:
		selList, slicedDfAtVarX = dx.interpolatedSlice(listOfDf, sliceVar, sliceVal)
		df =  slicedDfAtVarX[['r','jx', slicePlot]].copy()
		fig = go.Figure(data=[go.Surface(z=df.values)])
		fig.update_layout(title='3D '+slicePlot, autosize=False,
						width=700, height=700)
		return [fig]
	else:
		return [{}]


def gCompFilter(sliceVar, sliceVal, slicePlot, g_comp):

	global parsedDf, fileCheck, listOfDf 
	if fileCheck is True: 
		#print(g_comp)
		#print("plotted button:",listOfDf)
		for i, x in enumerate(listOfDf):
			listOfDf[i] = dx.filterOnCompressionThreshold(x, g_comp)


		return [{}]

	else:
		return [{}]

#----------------------------------------------------------------------------------#

@server.route("/LoadPull-Dashboard/")
def my_dash_app():
    return app.index()

def open_browser():
      webbrowser.open_new('http://127.0.0.1:8050/LoadPull-Dashboard/')

if __name__ == '__main__':
	Timer(1, open_browser).start();
	app.run_server(debug=True)

#----------------------------------------------------------------------------------#


