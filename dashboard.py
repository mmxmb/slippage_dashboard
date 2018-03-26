import dash
from dash.dependencies import Output, Event
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.graph_objs as go

from ws_connectors.bitfinex_order_book_ws import BitfinexOrderBookWS
from slippage_calculator import calc_slippage, get_quote_price

MONEY = 50000

subscribe_request_btc = dict( 
                        event='subscribe',
                        channel='book',
                        symbol='tBTCUSD',
                        prec='P0',
                        freq='F1',
                        len='25' 
                        )
subscribe_request_eth = dict( 
                        event='subscribe',
                        channel='book',
                        symbol='tETHUSD',
                        prec='P0',
                        freq='F1',
                        len='25' 
                        )
book_conn = BitfinexOrderBookWS()
book_conn.subscribe_to_channels([subscribe_request_btc, subscribe_request_eth])

app = dash.Dash(__name__)
app.layout = html.Div(
    [
        dcc.Graph(id='live-update-graph-bar', animate=True),
        dcc.Interval(
            id='interval-component',
            interval=1*1000
        ),
    ]
)

@app.callback(Output('live-update-graph-bar', 'figure'),
              events=[Event('interval-component', 'interval')])
def update_graph_scatter():
    traces = []
    if book_conn.books: # books is empty for a few secs at start
        btc_book = book_conn.books['tBTCUSD']
        eth_book = book_conn.books['tETHUSD']

        btc_quote_price = get_quote_price(btc_book, 'ask')
        eth_quote_price = get_quote_price(eth_book, 'ask')

        btc_volume = MONEY / btc_quote_price
        eth_volume = MONEY / eth_quote_price

        btc_slippage = calc_slippage(btc_book, btc_volume, 'ask')
        eth_slippage = calc_slippage(eth_book, eth_volume, 'ask')
        print([btc_slippage['slippage_cost'], eth_slippage['slippage_cost']])
        traces.append(plotly.graph_objs.Bar(
            x=[1],
            y=[btc_slippage['slippage_cost']],
            name='Bar'
        ))
        traces.append(plotly.graph_objs.Bar(
            x=[1],
            y=[eth_slippage['slippage_cost']],
            name='Bar'
        ))
        layout = plotly.graph_objs.Layout(
            barmode='group'
        )

        return {'data': traces, 'layout': layout}



if __name__ == '__main__':
    app.run_server(debug=True)