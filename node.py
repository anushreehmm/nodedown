import pandas as pd
import dash
import os
import re
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_table
import dash_bootstrap_components as dbc
import plotly.express as px

# Data Cleaning Functions
def data1_clean(file1_path):
    df = pd.read_excel(file1_path, skiprows=5)
    df = df.rename(columns={
        'Unnamed: 0': 'Sl.no',
        'Unnamed: 1': 'IP Address',
        'Unnamed: 4': 'Event',
        'Unnamed: 6': 'Alarm Time',
        'Unnamed: 2': 'Node Alias'  # Rename Host Name to Node Alias
    })
    df = df.drop(columns=['Sl.no', 'Clear Time', 'Duration', 'Description', 'Host Name'], errors='ignore')  # Dropping unnecessary columns
    df = df.dropna(subset=['Node Alias', 'Alarm Time'])  # Dropping rows with NaN in important columns
    df['Alarm Time'] = pd.to_datetime(df['Alarm Time'], errors='coerce')
    df = df.dropna(subset=['Alarm Time'])  # Ensure Alarm Time is datetime
    return df

def data2_clean(file2_path):
    df = pd.read_excel(file2_path)
    df = df.drop([0, 1, 2, 3, 4], axis=0).reset_index(drop=True)
    df = df.drop(columns=['Unnamed: 2', 'Unnamed: 3'], errors='ignore')
    df = df.rename(columns={
        'Unnamed: 0': 'Node Alias',
        'Unnamed: 1': 'IP Address',
        'Unnamed: 4': 'Availability',
        'Unnamed: 5': 'Latency(msec)',
        'Unnamed: 6': 'Packet Loss(%)'
    })
    df['Packet Loss(%)'] = pd.to_numeric(df['Packet Loss(%)'], errors='coerce')
    df['Availability'] = pd.to_numeric(df['Availability'], errors='coerce')
    df['Latency(msec)'] = pd.to_numeric(df['Latency(msec)'], errors='coerce')
    df = df.dropna(subset=['Packet Loss(%)', 'Availability', 'Latency(msec)'])
    return df

# File Paths
file1_path = 'data (2).xlsx'
file2_path = 'data2.xlsx'

# Cleaned DataFrames
df1_cleaned = data1_clean(file1_path)
df2_cleaned = data2_clean(file2_path)

# Merge DataFrames on 'IP Address', adding 'Availability' to df1
merged_df = pd.merge(df1_cleaned, df2_cleaned[['IP Address', 'Availability']], on='IP Address', how='left')
# downtime_count = (
#     merged_df.groupby('Node Alias')['Alarm Time']
#     .nunique()
#     .reset_index(name='Downtime Count')
# )

app = dash.Dash(__name__, 
    external_stylesheets=[
        "https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css",
        dbc.themes.CYBORG  # Optional, you can use other Bootstrap themes
    ]
)
def layout_home():
    return dbc.Container(
        fluid=True,
        style={"backgroundColor": "#f5f5f5", "minHeight": "100vh", "padding": "20px"},
        children=[
            # Header
            dbc.Row(
                dbc.Col(
                    html.H1(
                        "Node Availability Report",
                        className="text-center text-light bg-primary p-4 mb-4 rounded",
                        style={"fontSize": "36px", "font-family": "Roboto, sans-serif"}
                    ),
                    width=12
                )
            ),
            # Filters Section
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Label("Select Date Range:", style=custom_label_style),
                            dcc.DatePickerRange(
                                id='date-range',
                                start_date=min_date.date(),
                                end_date=max_date.date(),
                                min_date_allowed=min_date.date(),
                                max_date_allowed=max_date.date(),
                                display_format='YYYY-MM-DD',
                                style=custom_dropdown_style
                            )
                        ],
                        width=4
                    ),
                    dbc.Col(
                        [
                            html.Label("Select Downtime Count:", style=custom_dropdown_style),
                            dcc.Dropdown(
                                id='downtime-dropdown',
                                options=[
                                    {'label': '1-3', 'value': '1-3'},
                                    {'label': '4-5', 'value': '4-5'},
                                    {'label': '>5', 'value': '>5'},
                                    {'label': '>10', 'value': '>10'}
                                ],
                                value='1-3',  # Default value
                                placeholder='Select downtime count criteria',
                                style=custom_dropdown_style
                            )
                        ],
                        width=4
                    ),
                    dbc.Col(
                        [
                            html.Br(),
                            dbc.Button("Apply Filters", id='filter-button', color="success")
                        ],
                        width=4
                    )
                ],
                className="mb-4"
            ),
            # Data Table Section
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader(html.H4("Filtered Node Availability")),
                            dbc.CardBody(
                                dash_table.DataTable(
                                    id='filtered-table',
                                    columns=[
                                        {'name': 'Node Alias', 'id': 'Node Alias'},
                                        {'name': 'Availability', 'id': 'Availability'}
                                    ],
                                    style_table={'overflowX': 'auto'},
                                    style_cell={
                                        'textAlign': 'left',
                                        'padding': '10px',
                                        'backgroundColor': '#2c2c2c',
                                        'color': 'white'
                                    },
                                    style_header={
                                        'backgroundColor': '#1a1a1a',
                                        'color': 'white',
                                        'fontWeight': 'bold'
                                    },
                                    style_as_list_view=True,
                                    page_size=20,
                                    sort_action='native',
                                    filter_action='native',
                                )
                            )
                        ],
                        className="shadow-lg"
                    ),
                    width=12
                )
            )
        ]
    )

# Layout for the Detailed Graph Page
def layout_details(node_alias):
    return dbc.Container(
        fluid=True,
        style={"backgroundColor": "#f5f5f5", "minHeight": "100vh", "padding": "20px"},
        children=[
            dbc.Row(
                dbc.Col(
                    html.H2(f"Details for Node Alias: {node_alias}", 
                            className="text-center text-light bg-secondary p-3 mb-4 rounded"),
                    width=12
                )
            ),
            dbc.Row(
                [
                    # Packet Loss Graph
                    dbc.Col(
                        dcc.Graph(id='packet-loss-graph'),
                        width=6
                    ),
                    # Latency Graph
                    dbc.Col(
                        dcc.Graph(id='latency-graph'),
                        width=6
                    ),
                ]
            ),
            dbc.Row(
                [
                    # Availability Graph
                    dbc.Col(
                        dcc.Graph(id='availability-graph'),
                        width=6
                    ),
                    # Downtime Timeline
                    dbc.Col(
                        dcc.Graph(id='downtime-timeline-graph'),
                        width=6
                    ),
                ]
            ),
            dbc.Row(
                dbc.Col(
                    dcc.Link("Back to Report", href="/", className="btn btn-primary")
                )
            )
        ]
    )

# Main App Layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

# Callbacks for Page Routing
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    if pathname == '/':
        return layout_home()
    elif pathname.startswith('/details/'):
        node_alias = pathname.split('/')[-1]
        return layout_details(node_alias)
    else:
        return "404 Page Not Found"

# Callback to Update Table and Add Clickable Node Alias Links
@app.callback(
    Output('filtered-table', 'data'),
    [Input('filter-button', 'n_clicks')],
    [State('date-range', 'start_date'),
     State('date-range', 'end_date'),
     State('downtime-dropdown', 'value')]
)
def update_table(n_clicks, start_date, end_date, downtime_criteria):
    # Filter logic as before...
    # Generate clickable links
    filtered_df['Node Alias'] = filtered_df['Node Alias'].apply(
        lambda alias: dcc.Link(alias, href=f'/details/{alias}')
    )
    return filtered_df.to_dict('records')

# Callbacks for Graph Generation on Detailed Page
@app.callback(
    [Output('packet-loss-graph', 'figure'),
     Output('latency-graph', 'figure'),
     Output('availability-graph', 'figure'),
     Output('downtime-timeline-graph', 'figure')],
    Input('url', 'pathname')
)
def update_graphs(pathname):
    node_alias = pathname.split('/')[-1]
    # Filter data based on Node Alias
    node_data = merged_df[merged_df['Node Alias'] == node_alias]
    
    # Packet Loss Graph
    packet_loss_fig = px.line(node_data, x='Alarm Time', y='Packet Loss(%)', title='Packet Loss over Time')
    
    # Latency Graph
    latency_fig = px.line(node_data, x='Alarm Time', y='Latency(msec)', title='Latency over Time')
    
    # Availability Graph
    availability_fig = px.line(node_data, x='Alarm Time', y='Availability', title='Availability over Time')
    
    # Downtime Timeline (using Alarm Time as a proxy)
    downtime_fig = px.timeline(node_data, x_start="Alarm Time", title='Downtime Timeline')

    return packet_loss_fig, latency_fig, availability_fig, downtime_fig

# Run the app
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run_server(host="0.0.0.0", port=port, debug=True)
