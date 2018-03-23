import json
import asyncio
import websockets
import queue
import threading

async def subscribe(ws_host, subscribe_request, q):
    async with websockets.connect(ws_host) as ws:
        request = json.dumps(subscribe_request)
        await ws.send(request)
        while True:
            try:
                message = await ws.recv()
                q.put(message)
            except websockets.exceptions.ConnectionClosed:
                print("Connection was closed")


def initiate_subscriptions(q):
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
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    #loop = asyncio.get_event_loop()
    tasks = [subscribe(ws_host, subscribe_request_btc, q), subscribe(ws_host, subscribe_request_eth, q)]
    loop.run_until_complete(asyncio.wait(tasks))
    loop.close()

q = queue.Queue()
t1 = threading.Thread(target=initiate_subscriptions, name=initiate_subscriptions, args=(q,))
t1.start()

while True:
    value = q.get()
    print(value)