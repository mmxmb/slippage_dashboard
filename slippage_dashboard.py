import dash
from dash.dependencies import Output, Event
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import plotly.graph_objs as go
from collections import deque
import queue
import asyncio
import threading
from ws_connectors.bitfinex_ws import subscribe
from slippage_calculator import calc_slippage

X = deque(maxlen=20)
X.append(1)
Y = deque(maxlen=20)
Y.append(1)


app = dash.Dash(__name__)
app.layout = html.Div(
    [
        dcc.Graph(id='live-graph', animate=True),
        dcc.Interval(
            id='graph-update',
            interval=1*1000
        ),
    ]
)

@app.callback(Output('live-graph', 'figure'),
              events=[Event('graph-update', 'interval')])
def update_graph_scatter():
    X.append(X[-1]+1)
    #Y.append(Y[-1]+Y[-1]*random.uniform(-0.1,0.1))

    data = plotly.graph_objs.Scatter(
            x=list(X),
            y=list(Y),
            name='Scatter',
            mode= 'lines+markers'
            )

    return {'data': [data],'layout' : go.Layout(xaxis=dict(range=[min(X),max(X)]),
                                                yaxis=dict(range=[min(Y),max(Y)]),)}

def fetch_slippage(queues):
    while True:
        for queue in queues:
            if queue.empty():
                pass
            else:
                book = queue.get(block=False)
                slippage = calc_slippage(book, 15, 'bid')
                print(slippage['slippage_cost'])
                Y.append(slippage['slippage_cost'])


if __name__ == '__main__':
    ws_host = 'wss://api.bitfinex.com/ws/2'
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
    q_btcusd = queue.Queue()
    q_ethusd = queue.Queue()
    loop = asyncio.get_event_loop()
    tasks = [subscribe(ws_host, subscribe_request_btc, q_btcusd), subscribe(ws_host, subscribe_request_eth, q_ethusd)]
    t1 = threading.Thread(target=loop.run_until_complete, args=(asyncio.wait(tasks),), daemon=True)
    t1.start()
    t2 = threading.Thread(target=fetch_slippage, args=([q_btcusd, q_ethusd],), daemon=True)
    t2.start()
    app.run_server(debug=True)
   
    loop.close()