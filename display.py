import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import pandas as pd
import plotly.express as px
from dash.dependencies import Input, Output
from hemlock import Dashboard
try:
    from yaml import load, CLoader as Loader
except:
    from yaml import load, Loader

# number of time steps to display
DISPLAY_TIME_STEPS = 60

# load forecast questions
forecast_questions = load(open('forecasts.yaml', 'r'), Loader=Loader)

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

    def make_graphs(key):
        from survey import TIME_STEPS

        def make_graph(df, title, labels):
            return dcc.Graph(
                id='graph',
                figure=px.line(
                    df, x='Time', y='y', title=title, labels=labels
                )
            )

        content = forecast_questions[key]
        df = pd.read_csv(content['filename'])
        df = df.iloc[-DISPLAY_TIME_STEPS-TIME_STEPS:]
        df['y'].iloc[-TIME_STEPS:] = None
        df_no_context = df.copy()
        df_no_context['Time'] = list(range(len(df)))
        return {
            False: make_graph(
                df_no_context,
                title='Untitled graph', 
                labels={'Time': 'Time', 'y': 'Units'}
            ),
            True: make_graph(
                df,
                title=content['title'],
                labels={'Time': content['x'], 'y': content['y']}
            )
        }

    graphs = {key: make_graphs(key) for key in forecast_questions.keys()}

    @dash_app.callback(
        Output('graph-container', 'children'),
        [Input('url', 'search')]
    )
    def load_graph(search):
        if app is None:
            print('WARNING: No dashboard located')
            return [graphs['COVID_cases'][True]]
        g = Dashboard.get(search).g
        return [graphs[g['fcast_key']][g['context']]]

    return dash_app

if __name__ == '__main__':
    make_dashboard().run_server(debug=True)