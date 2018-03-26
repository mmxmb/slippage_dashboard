import dash
from dash.dependencies import Output, Event, Input
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.graph_objs as go
import requests
import sys
import re
import ast
from random import random

from ws_connectors.bitfinex_order_book_ws import BitfinexOrderBookWS
from slippage_calculator import calc_slippage, get_quote_price
"""
resp = requests.get('https://api.bitfinex.com/v1/symbols')
if resp.status_code == 200:
    bitfinex_all_symbols = ast.literal_eval(resp.content.decode())
else:
    print('Cannot get list of Bitfinex symbols')
    sys.exit(1)

bitfinex_usd_symbols = [x for x in bitfinex_all_symbols if re.match(r'.*usd$', x)] # look like: 'btcusd', 'ltcusd' etc.
book_sub_usd_symbols = ['t' + x.upper() for x in bitfinex_usd_symbols] # now look like: 'tBTCUSD', 'tLTCUSD' etc.

# see reference here https://bitfinex.readme.io/v2/reference#ws-public-order-books
subscribe_request_template = dict( 
                                  event='subscribe',
                                  channel='book',
                                  symbol='',
                                  prec='P0',
                                  freq='F1',
                                  len='25' 
                                 )
subscribe_requests = [dict(subscribe_request_template, symbol=s) for s in book_sub_usd_symbols]

try:
    book_conn = BitfinexOrderBookWS()
    book_conn.subscribe_to_channels(subscribe_requests)
except SystemExit as e:
    print(e)
    sys.exit(1)
"""
app = dash.Dash(__name__)

colors = {
    'app_background': '#001122',
    'graph_background': '#112233',
    'text': '#99ccff',
    'input_box': '#778899'
}

app.layout = html.Div(
          style={'backgroundColor': colors['app_background'], 'fontFamily': 'Arial', 'margin':'-30px'}, 
          children=[
                    html.H1('Live Slippage on Bitfinex USD Pairs', style={
                                                                          'textAlign': 'center',
                                                                          'color': colors['text'],
                                                                          'margin-top': '30px'
                                                                          }),
                    html.Div(
                            style={'marginLeft': '50px'},
                            children =[
                                        html.P('Market Order Cost (USD)', style={
                                                                     'textAlign': 'left',
                                                                     'color': colors['input_box']
                                                                    }),
                                        dcc.Input(
                                                  id='cost', 
                                                  value=1000, 
                                                  type='text', 
                                                  style={'backgroundColor': colors['input_box']}),
                                        dcc.RadioItems(
                                                       id='market_side',
                                                       options=[
                                                                {'label': 'Ask', 'value': 'ask'},
                                                                {'label': 'Bid', 'value': 'bid'}
                                                               ],
                                                       value='ask',
                                                       style={'color': colors['input_box'],},
                                                       labelStyle={'marginLeft': '10px', 'marginRight': '10px'}
                                                      )
                                    ]),
                    html.Div(className='row', children=[
                                                        html.Div(dcc.Graph(id='live-update-graph-bar'), className='col s12 m6 l6'),
                                                        html.Div(dcc.Graph(id='table'), className='col s12 m6 l6')
                                                        ]),
                    dcc.Interval(
                                id='interval-component',
                                interval=1*1000
                                )
                    ])


@app.callback(Output('table', 'figure'),
              events=[Event('interval-component', 'interval')])
def update_table():
    trace = go.Table(
    header=dict(values=['Pair', 'Quote Price'],
                line = dict(color='#7D7F80'),
                fill = dict(color='#a1c3d1'),
                align = ['left'] * 5),
    cells=dict(values=[[100, 90, 80, 90],
                       [95, 85, 75, 95]],
               line = dict(color='#7D7F80'),
               fill = dict(color='#EDFAFF'),
               align = ['left'] * 5))

    layout = dict(width=500, height=300)
    return {'data': [trace], 'layout': layout}


@app.callback(Output('live-update-graph-bar', 'figure'),
            [Input(component_id='cost', component_property='value'),
            Input(component_id='market_side', component_property='value')],
              events=[Event('interval-component', 'interval')])
def update_graph_bar(cost, market_side):
    """
    if book_conn:
        X = []
        for book in book_conn.books.values():
            quote_price = get_quote_price(book, market_side)
            quote_volume = float(cost) / quote_price
            slippage = calc_slippage(book, quote_volume, market_side)
            X.append(slippage['slippage_frac'])
        Y = list(book_conn.books.keys())
    """

    traces = list()
    for t in range(1):
        traces.append(go.Bar(
            x=[random() * 100 for i in range(30)],
            y=[x for x in range(30)],
            name='Bar {}'.format(t),
            orientation = 'h'
            ))
    layout = plotly.graph_objs.Layout(
    plot_bgcolor=colors['graph_background'],
    paper_bgcolor=colors['app_background'],
    font=dict(color=colors['text']),
    barmode='group',
    height=650,
    width=900,
    xaxis=dict(
               range=[0,100],
               title='% Slippage (Slippage Cost over Order Cost)',
               ),
    margin=dict(t=0)
)
    return {'data': traces, 'layout': layout}


if __name__ == '__main__':
    app.css.append_css(
        {'external_url': 'https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.0.0/css/bootstrap.min.css'}
    )
    app.run_server(debug=True)