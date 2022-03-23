import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from styles import style

business_univariate_df = pd.read_csv('./data/business_univariate_stats.csv')
workers_univariate_df = pd.read_csv('./data/workers_univariate_stats.csv')
business_bivariate_df = pd.read_csv('./data/business_bivariate_stats.csv')
workers_bivariate_df =  pd.read_csv('./data/workers_bivariate_stats.csv')

business_variables_map = pd.read_excel('./data/generated_business_variable_map.xlsx')
business_variables_map.loc[business_variables_map['group']=='general', 'queue_index'] = [37, 38, 39]
business_variables_map.sort_values('queue_index', inplace=True)

workers_variables_map = pd.read_excel('./data/generated_workers_variable_map.xlsx')

groups = business_univariate_df['variable_group'].unique()[1:]

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

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server


app.layout = dbc.Col(html.Div([
    html.Div([html.Div('C2M2', 
            style=style['c2m2']),
    html.Div('KATHMANDU', 
            style=style['kathmandu']),
        ], 
            style=style['header']),
    html.Br(),
    html.Div([
    dcc.Tabs(id='dropdown-survey', value='business', children=[
        dcc.Tab(label='Business', value='business', style=style['tab-1']),
        dcc.Tab(label='Workforce', value='workforce', style=style['tab-2']),
        ], style= style['tabs'])
    ]),
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
    dcc.Graph(id="bar-chart", style={'marginLeft': '10px'}, config=config),
]),md='12')

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
    Output("bar-chart", "figure"),
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

    group_df = df[df["variable_group"]==group.lower()]
    if filter != 'None':
        group_df = df[df["variable_group"]==group.capitalize()]
        group_df = group_df[group_df['x_variable']== filter]
    labels_df = labels_map[labels_map['group']==group.lower()]
    subplot_titles=labels_map[labels_map['group']==group.lower()]['ques__en'].values
    variables = labels_df['variable'].unique()
    fig = make_subplots(rows=len(variables), cols=1,
    subplot_titles=subplot_titles, vertical_spacing = 0.2/len(variables))
    if filter != 'None':
        data = group_df[group_df['y_variable']=='i_covid_effect_business']
        fig = px.bar(
                x=data['total'],
                y=data['y_label__en'],
                color=data['x_label__en'])
        fig.update_layout(
            height=(600), 
            width=1200,
        )
        # for idx , i in enumerate(variables):
        #     label_cond=list(labels_map[labels_map['variable']==i]['asked_condition'])[0]
        #     label_total=list(labels_map[labels_map['variable']==i]['asked_total'])[0]
        #     if label_cond =='general':
        #         total = 'showing '+str(label_total)+ ' responses'
        #     else:
        #         total = 'showing '+str(label_total) + ' responses of ' + label_cond
        #     mask = group_df[group_df['y_variable']==i]
        #     dt = {}
        #     for i in mask['x_label__en'].unique():
        #         dt[i] = mask[mask['x_label__en']==i]['total'].values.tolist()
        #     dt['label'] = mask['y_label__en'].unique().tolist()

        #     data = dt,
        #     traces = []
        #     base = [0,0,0,0,0]
        #     for key in list(data[0].keys())[:-1]:
        #         traces.append(go.Bar(
        #             name = key,
        #             x = data[0][key],
        #             y = data[0]['label'],
        #             offsetgroup = 1,
        #             base=base,
        #             orientation='h',
        #             showlegend=True
        #         ))
        #         base = [val1+val2 for val1, val2 in zip(base, data[0][key])]
        #     figure = go.Figure(
        #         data=traces,
        #         layout=go.Layout(
        #             title="Issue Types - Original and Models",
        #             yaxis_title="Number of Issues"
        #         )
        #     )
        #     for trc in figure['data']:
        #         fig.add_trace(trc, row=idx+1, col=1)
        #     fig.update_xaxes(title_text=total, row=idx+1, col=1)
        #     fig.update_yaxes(ticklabelposition='inside')
        #     fig.update_layout(
        #     height=(600* len(variables)), 
        #     width=1200,
        # )
    else:
        for idx, i in enumerate(variables):
            label_cond=list(labels_map[labels_map['variable']==i]['asked_condition'])[0]
            label_total=list(labels_map[labels_map['variable']==i]['asked_total'])[0]
            if label_cond =='general':
                total = 'showing '+str(label_total)+ ' responses'
            else:
                total = 'showing '+str(label_total) + ' responses of ' + label_cond
            mask = group_df['variable']==i
            fig.add_trace(go.Bar( 
                x=group_df[mask]["total"], 
                y=group_df[mask]["label__en"],
                orientation='h',
                marker_color = 'rgba(79, 167, 159, 0.726)',
                ), row=idx+1, col=1)
            fig.update_xaxes(title_text=total, row=idx+1, col=1)
        fig.update_yaxes(ticklabelposition='inside')
        fig.update_layout(
            height=(600* len(variables)), 
            width=1200,
            showlegend=False,
        )
    return fig
if __name__ == '__main__':
    app.run_server(debug=True)
