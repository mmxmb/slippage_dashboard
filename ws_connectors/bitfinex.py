import json
import asyncio
import websockets
import sys
# INFO CODES
# 20051 - reconnect/restart
# 20060 - maintenance start (pause all activity)
# 20061 - maintenance end (resume all activity)


NO_ASKS_AT_LEVEL = -1
NO_BIDS_AT_LEVEL = 1

channel_symbols = {}
books = {}
# price level (key) -> 


async def subscribe(ws_host, subscribe_request):
    async with websockets.connect(ws_host) as ws:
        request = json.dumps(subscribe_request)
        await ws.send(request)
        # event is dict type, data is list type
        is_event = lambda o: isinstance(o, dict)
        is_data= lambda o: isinstance(o, list)
        while True:
            try:
                message = await ws.recv()
                message = json.loads(message)
                if is_event(message):
                    handle_event(message)
                elif is_data(message):
                    book = handle_data(message)
                else:
                    print('Unknown message type')
            except websockets.exceptions.ConnectionClosed:
                print("Connection was closed")

def handle_event(event):
    event_type = event['event']
    if event_type == 'info':
        # try getting info code
        try:
            info_code = event['code']
        except KeyError:
            info_code = None
        if info_code:
            pass
    elif event_type == 'subscribed':
        channel_id = event['chanId'] # int
        channel_symbol = event['symbol']
        channel_symbols[channel_id] = channel_symbol
        books[channel_symbol] = {
                                'bids': {},
                                'asks': {}
                                }

def get_channel_id(data):
    """ Channel id is always the first element in snapshot/update list """
    assert isinstance(data, list)
    assert len(data) > 1
    return data[0]

def get_stream_fields(data):
    """ Stream fields list is always the second element in snapshot/update list """
    assert isinstance(data, list)
    assert len(data) > 1
    # this is a snapshot
    if isinstance(data[1][0], list):
        return data[1]
    # this is an update
    elif isinstance(data[1][0], float) or isinstance(data[1][0], int):
        return [data[1]]

def update_order_book(book, stream_fields):
    try:
        for stream_field in stream_fields:
            assert len(stream_field) is 3
            price, count, amount  = stream_field
            # delete price level
            if count == 0:
                if amount == NO_ASKS_AT_LEVEL:
                    del book['asks'][price]
                elif amount == NO_BIDS_AT_LEVEL:
                    del book['bids'][price]
            else:
                if amount > 0:
                    book['bids'][price] = amount
                elif amount < 0:
                    amount = abs(amount) # easier to work with just positive mount
                    book['asks'][price] = amount
    except TypeError:
        print('ERROR')
    return book

def is_heartbeat(data):
    assert len(data) > 1
    if isinstance(data[1], str) and data[1] == 'hb':
        return True
    else:
        return False

def handle_data(data):
    """ Handle book snapshot or update"""
    if not is_heartbeat(data):
        channel_id = get_channel_id(data)
        symbol = channel_symbols[channel_id]
        book = books[symbol]
        stream_fields = get_stream_fields(data)
        book = update_order_book(book, stream_fields)
        books[symbol] = book
        print(book, '\n\n\n')

if __name__ == '__main__':
    ws_host = 'wss://api.bitfinex.com/ws/2'
    subscribe_request = dict( 
                            event='subscribe',
                            channel='book',
                            symbol='tBTCUSD',
                            prec='P0',
                            freq='F1',
                            len='25' 
                            )
    subscribe_request1 = dict( 
                            event='subscribe',
                            channel='book',
                            symbol='tETHUSD',
                            prec='P0',
                            freq='F1',
                            len='25' 
                            )
    #asyncio.get_event_loop().run_until_complete(subscribe(ws_host, subscribe_request))
    loop = asyncio.get_event_loop()
    tasks = [subscribe(ws_host, subscribe_request), subscribe(ws_host, subscribe_request1)]
    loop.run_until_complete(asyncio.wait(tasks))
    print('yea')
    loop.close()