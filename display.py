import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output
from hemlock import Dashboard

def make_dashboard(app=None):
    if app is not None:
        dash_app = dash.Dash(
            server=app,
            routes_pathname_prefix='/dashapp/',
            external_stylesheets=[dbc.themes.BOOTSTRAP]
        )
    else:
        dash_app = dash.Dash(
            external_stylesheets=[dbc.themes.BOOTSTRAP]
        )

    dash_app.layout = html.Div([
        dcc.Location(id='url', refresh=False),
        html.Div([
            dbc.Alert('Loading graph'),
        ], id='graph-container')
    ], className='container')

    @dash_app.callback(
        Output('graph-container', 'children'),
        [Input('url', 'search')]
    )
    def load_graph(search):
        content = Dashboard.get(search).g
        df = pd.read_csv(content['file_name'])
        if not content['use_context']:
            df['Time'] = np.arange(1, len(df)+1)
            title = 'Unitited graph'
            content_ = content['no_context']
        else:
            title = content['title']
            content_ = content['context']
        columns = {'Time': content_['x'], 'y': content_['y']}
        df = df.rename(columns=columns)
        return [dcc.Graph(
            id='graph', 
            figure=px.line(
                df, x=columns['Time'], y=columns['y'], title=title)
        )]

    return dash_app

if __name__ == '__main__':
    make_dashboard().run_server(debug=True)