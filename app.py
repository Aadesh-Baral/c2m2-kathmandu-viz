import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from styles import style
import dash_leaflet as dl
import dash_leaflet.express as dlx

business_univariate_df = pd.read_csv('./data/business_univariate_stats.csv')
workers_univariate_df = pd.read_csv('./data/workers_univariate_stats.csv')
business_bivariate_df = pd.read_csv('./data/business_bivariate_stats.csv')
workers_bivariate_df =  pd.read_csv('./data/workers_bivariate_stats.csv')

business_variables_map = pd.read_excel('./data/generated_business_variable_map.xlsx')
business_variables_map.loc[business_variables_map['group']=='general', 'queue_index'] = [37, 38, 39]
business_variables_map.sort_values('queue_index', inplace=True)

workers_variables_map = pd.read_excel('./data/generated_workers_variable_map.xlsx')

maps_df = pd.read_csv('./data/map_visualization_data.csv')
maps_variable = ()
groups = business_univariate_df['variablegroup'].unique()[:-1]

all_options = {
    'workforce': ['None'] + workers_variables_map[workers_variables_map['group']=='general']['variable'].values.tolist(),
    'business': ['None'] + business_variables_map[business_variables_map['group']=='general']['variable'].values.tolist()
}
filter_dict = {
    'm_gender': 'Gender', 
    'm_age': 'Age', 
    'm_edu_levl': 'Education', 
    'm_years_of_experience': 'Experience', 
    'm_biz_years_in_operation': 'Years in operation',
    'm_biz_type': 'Type',
    'b_n_emplyes_pre_covid': 'No of employees',
    'None': 'None'
}
config = {'displayModeBar': False}

# external_stylesheets = ['./style.css']

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

server = app.server

app.layout = dbc.Col(html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div([html.Div('C2M2', 
            style=style['c2m2']),
    html.Div('KATHMANDU', 
            style=style['kathmandu']),
         html.Div([dcc.Link('Charts', href='/charts', style=style['url']), dcc.Link('Maps', href='/maps', style=style['url'])], style=style['link'])],
            style=style['header']),
    html.Br(),
    html.Div(id='page-content')
]))

# Update the index
@app.callback(dash.dependencies.Output('page-content', 'children'),
              [dash.dependencies.Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/charts':
        return charts_layout
    elif pathname == '/maps':
        return maps_layout

charts_layout = html.Div([html.Div([
    dcc.Tabs(id='dropdown-survey', value='business', children=[
        dcc.Tab(label='Business', value='business', style=style['tab-1']),
        dcc.Tab(label='Workforce', value='workforce', style=style['tab-2']),
        ], style= style['tabs'])
    ]),
    dbc.Col([
    dbc.Row([
        dbc.Col([
            dbc.Label("Explore"),
            dcc.Dropdown(
                id="dropdown-research",
                options=[{"label": x.upper(), "value": x} for x in groups],
                value=groups[0],
                clearable=False
            )
        ], md=3),
        dbc.Col([
            dbc.Label("By"),
            dcc.Dropdown(
                id="dropdown-filter",
                options=[{"label": x.upper(), "value": x} for x in groups],
                value=groups[0],
                clearable=False
            )
        ], md=3)
    ],
        style= {'marginTop':'50px'}),
    html.Hr(),
    html.Br(),
    html.Div(id='charts')])])

map_variables = maps_df['variable'].unique().tolist()

@app.callback(
    Output('map-label', 'options'),
    Input('map-variable', 'value'))
def update_label(variable):
    return([{'label':i, 'value':i} for i in maps_df[maps_df['variable']==variable]['label_en'].unique().tolist()])

@app.callback(
    Output('map-label', 'value'),
    Input('map-label', 'options'))
def update_value(options):
    return options[0]['value']

controls = dbc.Card(
    [
        dbc.FormGroup(
            [
                dbc.Label("X variable"),
                dcc.Dropdown(
                    id="map-variable",
                    options=[{"label": col, "value": col} for col in map_variables],
                    value= map_variables[0],
                ),
            ]
        ),
        dbc.FormGroup(
            [
                dbc.Label("Y variable"),
                dcc.Dropdown(
                    id="map-label",
                ),
            ]
        ),
    ],
    body=True,
    style={'height': '85vh'}
)

@app.callback(
    Output('maps', 'children'),
    Input('map-label', 'value'))
def update_maps(label):
    maps_df_unique = maps_df[maps_df['label_en']==label].drop_duplicates(subset='coordinates')
    map = dl.Map([
        dl.TileLayer(),
        dl.GeoJSON(data=dlx.dicts_to_geojson([dict(lat=lat, lon=lon) for lat, lon in maps_df_unique[['latitude', 'longitude']].values.tolist()]), 
        cluster=True, zoomToBoundsOnClick=True, superClusterOptions={"radius": 100}),
    ], center=[28.5, 84], zoom=7, minZoom=7, style={'width': '100%', 'height': '85vh', 'margin': "auto", "display": "block"})
    return map

maps_layout = html.Div([dbc.Row([
                controls,
                dbc.Col(id='maps', md=9)])], style=style['tabs'])

@app.callback(
    Output('dropdown-filter', 'options'),
    Input('dropdown-survey', 'value'))
def set_cities_options(selected_country):
    return [{'label': filter_dict[i], 'value': i} for i in all_options[selected_country]]

@app.callback(
    Output('dropdown-filter', 'value'),
    Input('dropdown-filter', 'options'))
def set_cities_value(available_options):
    return available_options[0]['value']

@app.callback(
    Output("charts", "children"),
    [   Input("dropdown-survey", "value"),
        Input("dropdown-research", "value"),
        Input("dropdown-filter", "value")
    ])
def update_bar_chart(survey, group, filter):
    if survey=='business':
        if filter == "None":
            df = business_univariate_df
        else:
            df = business_bivariate_df
        labels_map = business_variables_map
    elif survey=='workforce':
        if filter == "None":
                df = workers_univariate_df
        else:
            df = workers_bivariate_df
        labels_map = workers_variables_map

    group_df = df[df["variablegroup"]==group.lower()]
    if filter != 'None':
        group_df = df[df["variablegroup"]==group.lower()]
        group_df = group_df[group_df['xvariable']== filter]
    labels_df = labels_map[labels_map['group']==group.lower()]
    subplot_titles=labels_map[labels_map['group']==group.lower()]['ques_en'].values
    subgroup = labels_map[labels_map['group']==group.lower()]['subGroups'].values
    plot_titles = labels_map[labels_map['group']==group.lower()]['highlights'].values
    variables = labels_df['variable'].unique()
    if filter != 'None':
        output=[]
        for idx , i in enumerate(variables):
            label_cond=list(labels_map[labels_map['variable']==i]['askedCondition'])[0]
            label_total=list(labels_map[labels_map['variable']==i]['askedTotal'])[0]
            if label_cond =='general':
                total = 'showing '+str(label_total)+ ' responses'
            else:
                total = 'showing '+str(label_total) + ' responses of ' + label_cond
            data = group_df[group_df['yvariable']==i]
            fig = px.bar(
                    x=data['total'],
                    y=data['ylabel_en'],
                    color=data['xlabel_en'],
                   )
            fig.update_xaxes(title_text=total, autorange=False, range=[0,100])
            fig.update_yaxes(ticklabelposition='inside', color='white')
            fig.update_layout(
                plot_bgcolor = "rgb(250, 250, 250)",
                title = subplot_titles[idx],
                height=(600), 
                width=830,
            )
            output.append(
                html.Div(
                    [dbc.Col([
                        dbc.Row([
                            dbc.Col([
                                html.H5(subgroup[idx],style={'color':'rgb(189, 34, 34)', 'marginTop':'50px', 'fontFamily': 'Benne'} ),
                                html.H3(plot_titles[idx], style={'color':'rgb(189, 34, 34)', 'fontWeight':'Bold', 'fontFamily': 'Dosis'})
                                ],style={'backgroundColor': 'rgb(235, 235, 235)'} ,md=4),
                            dbc.Col(
                                dcc.Graph(id=i,figure =fig,config=config), md=8)
                            ])
                            ], style={'boxShadow': '0px 1px 5px 1px #ccc'}), 
                        html.Br(), 
                        html.Br(), 
                        html.Br()
                    ], style={'marginLeft': '80px', 'marginRight':'80px'}
                )
            )
            	
    else:
        output = []
        for idx, i in enumerate(variables):
            label_cond=list(labels_df[labels_df['variable']==i]['askedCondition'])[0]
            label_total=list(labels_map[labels_map['variable']==i]['askedTotal'])[0]
            if label_cond =='general':
                total = 'showing '+str(label_total)+ ' responses'
            else:
                total = 'showing '+str(label_total) + ' responses of ' + label_cond
            data = group_df[group_df['variable']==i]
            fig = px.bar(
                    x=data['percoftotal']*100,
                    y=data['label_en'],
                    color_discrete_sequence = ['rgb(189, 80, 80)']*len(data))
            fig.update_xaxes(title_text=total, autorange=False, range=[0,100])
            fig.update_yaxes(ticklabelposition='inside', color='white')
            fig.update_layout(
                plot_bgcolor = "rgb(250, 250, 250)",
                title = subplot_titles[idx],
                height=(600), 
                width=830,
            )
            output.append(
                html.Div(
                    [dbc.Col([
                        dbc.Row([
                            dbc.Col([
                                html.H5(subgroup[idx],style={'color':'rgb(189, 34, 34)', 'marginTop':'50px', 'fontFamily': 'Benne'} ),
                                html.H3(plot_titles[idx], style={'color':'rgb(189, 34, 34)', 'fontWeight':'Bold', 'fontFamily': 'Dosis'})
                                ],style={'backgroundColor': 'rgb(235, 235, 235)'} ,md=4),
                            dbc.Col(
                                dcc.Graph(id=i,figure =fig,config=config), md=8)
                            ])
                            ], style={'boxShadow': '0px 1px 5px 1px #ccc'}), 
                        html.Br(), 
                        html.Br(), 
                        html.Br()
                    ], style={'marginLeft': '80px', 'marginRight':'80px'}
                )
            )
    return output


if __name__ == '__main__':
    app.run_server(debug=True)
