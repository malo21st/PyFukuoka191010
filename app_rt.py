import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
from dash.dependencies import Input, Output
import plotly.graph_objs as go

import pandas as pd
import datetime

import serial
import re
import time

ACCEL_MAX =  2100
ACCEL_MIN = -2100
# gaugeゲージの色合い
BZ = [ACCEL_MIN, ACCEL_MAX/10]
GZ = [ACCEL_MAX/10, ACCEL_MAX/2] 
YZ = [ACCEL_MAX/2 , ACCEL_MAX*9/10] 
RZ = [ACCEL_MAX*9/10, ACCEL_MAX] 
COLOR = {"gradient":True,"ranges":{"blue":BZ,"green":GZ,"yellow":YZ,"red":RZ}}

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets = external_stylesheets)

ser = serial.Serial('/dev/cu.usbmodem141202', 115200, timeout = 1)
data = pd.DataFrame([[0,0,0,0]],columns = ['time','x','y','z'])

app.layout = html.Div(
    style = {'color': 'black', 'background-color': 'white'},
    children = [
    html.H1(children = 'リアルタイムデータの見える化'),

    html.H3(children = '''
        micro:bit 3次元加速度センサーの値を見える化しています。
    '''),
    dcc.Checklist(
        id = 'ax-checklist',
        options = [
            {'label': 'X方向の加速度 ', 'value': 'x'},
            {'label': 'Y方向の加速度 ', 'value': 'y'},
            {'label': 'Z方向の加速度 ', 'value': 'z'}
        ],
        value = ['x', 'y', 'z'],
        labelStyle = {'display': 'inline-block',
                    'paddingLeft' : 20,
                    'fontSize': '20px'
                    }
    ),
    html.Div(id = 'get_data'),
    dcc.Interval(id = 'timer', interval = 500),
    dcc.Graph(id = 'graph-with-checkbox'),
    html.Div([
	    daq.Gauge(
	    	id = 'x-gauge',
			showCurrentValue = True,
			color = COLOR,
			max = ACCEL_MAX,
			min = ACCEL_MIN,
			value = 0,
			label = 'X AXIS'
			),
	    daq.Gauge(
	    	id = 'y-gauge',
			showCurrentValue = True,
            color = COLOR,
			max = ACCEL_MAX,
			min = ACCEL_MIN,
			value = 0,
			label = 'Y AXIS'
			),
	    daq.Gauge(
	    	id = 'z-gauge',
			showCurrentValue = True,
            color = COLOR,
			max = ACCEL_MAX,
			min = ACCEL_MIN,
			value = 0,
			label = 'Z AXIS'
			)
	], style = {'columnCount': 3})
])

@app.callback(output = Output('get_data', 'children'),
              inputs = [Input('timer', 'n_intervals')])
def get_data(interval):
    global data
    global ser
    lst_data = []
    try:
        raw_data = ser.readline()
        txt_data = raw_data.strip().decode('utf-8')
        tmp_data = re.split( '[,\n]',txt_data)
        lst_data = [int(i) for i in tmp_data]
    except: # 読み取りエラーの時は、前の値を適用
        lst = data.iloc[-1]
        lst_data = [lst['x'],lst['y'],lst['z']]
    if len(lst_data) < 3: # データ数が欠損した時は、前の値を適用
        lst = data.iloc[-1]
        lst_data = [lst['x'],lst['y'],lst['z']]

    time = datetime.datetime.now()
    acl_x = lst_data[0]
    acl_y = lst_data[1]
    acl_z = lst_data[2]

    sr_data = pd.Series([time,acl_x,acl_y,acl_z], index=data.columns)
    data = data.append(sr_data, ignore_index=True)
    style = {'padding': '5px', 'fontSize': '20px'}

    return [
        html.Span('DayTime:  {}'.format(time), style=style),
        html.Span('  x_axis: {}'.format(acl_x), style=style),
        html.Span('  y_axis: {}'.format(acl_y), style=style),
        html.Span('  z_axis: {}'.format(acl_z), style=style)
    ]

@app.callback(
    Output('graph-with-checkbox', 'figure'),
    [Input('ax-checklist', 'value'),
    Input('timer', 'n_intervals')
    ]
)
def updateBarChart(checked_ax, interval):
    acl = {'x':'red', 'y':'green', 'z':'blue'}
    traces = []
    for ax in checked_ax:
        traces.append({
            'mode': 'lines',
            'type': 'scatter',
            'x' : data.loc[:,'time'][-10:],
            'y' : data.loc[:,ax][-10:],
            'marker' : {
                'color' : acl[ax],
            'line' : {'width' : 2,
                      'color' : 'blue'}},
            'orientation' : 'v',
            'name' : ax
        })
    layout = go.Layout(
    		yaxis = {'range' : [2100, -2100]}
    	)
    fig_bar = {'data' : traces, 'layout' : layout}
    return fig_bar

@app.callback(Output('x-gauge', 'value'),[Input('timer', 'n_intervals')])
def updateGauge_X(interval):
	return int(data.tail(1)['x'])
	
@app.callback(Output('y-gauge', 'value'),[Input('timer', 'n_intervals')])
def updateGauge_Y(interval):
	return int(data.tail(1)['y'])

@app.callback(Output('z-gauge', 'value'),[Input('timer', 'n_intervals')])
def updateGauge_Z(interval):
	return int(data.tail(1)['z'])

if __name__ == '__main__':
    print("========APP START ========")
    app.run_server(debug = True)
    ser.close()
    print("========APP STOP ========")
