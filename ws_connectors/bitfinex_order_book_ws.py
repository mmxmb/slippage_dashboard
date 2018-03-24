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

class BitfinexOrderBookWS:

    def __init__(self):
        """

        Attributes:
            ws_host: A string representing a websocket (ws) endpoint to an exchange.
            books: An empty dict that will be populated with snapshots
                    of order books of trading pairs of interest and is continuously
                    updated as long as ws connections are alive. Do not write to
                    this dictionary. It's intended to act as a single one-way 
                    channel between the thread running async ws connections to
                    the exchange and other threads elsewhere in the code:
                    the thread in subscribe_to_channels() writes to channel, 
                    other threads read it.

                    Example books dict after program ran for some time (tracking
                    state of two trading pairs):
                        books = {
                                'tBTCUSD': {
                                            'bid': {1000: 5, 500: 2},
                                            'ask': {400: 3, 550: 4}
                                           },
                                'tETHUSD': {
                                            'bid': {1100: 6, 650: 3},
                                            'ask': {40: 9, 250: 5}
                                           }
                                }
            _channel_symbols: A dict that maps channel ids to channel trading
                pair symbols. E.g.: {12777: 'tETHUSD', 21246: 'tBTCUSD'}
                Do not modify this dict.

                Channel id is some arbitrary(?) id that Bitfinex assigns
                to a channel once ws connection is established and
                then includes this id in every subsequent message on
                that channel. 

                Trading pair symbol is the same as 'symbol' value
                from the subscribe request to the channel. E.g:
                tBTCUSD for trading pair BTCUSD.

        """
        self.ws_host = 'wss://api.bitfinex.com/ws/2'
        self.books = {}
        self._channel_symbols = {}



    def subscribe_to_channels(self, subscribe_requests):
        """Subscribe to multiple order book websocket channels and keep up-to-date snapshots in books.

        This function creates asynchronous connections to multiple ws channels to
        keep track of order book state of multiple trading pairs. Each connection
        listens for updates indefinitely so all the connections are ran in a separate
        daemon thread.
            
            Args:
                subscribe_requests: A list of dicts representing subscription requests
                    to the ws endpoint. Each dict contains info like pair name and
                    update frequency. See more in the API docs: 
                    https://bitfinex.readme.io/v2/reference#ws-public-order-books

        """
        tasks = [self.subscribe(request) for request in subscribe_requests]
        loop = asyncio.get_event_loop()
        # run as daemon so that thread gets destroyed if main thread terminates
        t = threading.Thread(target=loop.run_until_complete, args=(asyncio.wait(tasks),), daemon=True)
        t.start()

    async def subscribe(self, subscribe_request):
        async with websockets.connect(self.ws_host) as ws:
            request = json.dumps(subscribe_request)
            await ws.send(request)
            # event is dict type, data is list type
            is_event = lambda o: isinstance(o, dict)
            is_data = lambda o: isinstance(o, list)
            while True:
                try:
                    message = await ws.recv()
                    message = json.loads(message)
                    if is_event(message):
                        self.handle_event(message)
                    elif is_data(message):
                        self.handle_data(message)
                    else:
                        print('Unknown message type')
                except websockets.exceptions.ConnectionClosed:
                    print("Connection was closed")

    def handle_event(self, event):
        event_type = event['event']
        if event_type == 'info':
            # TODO: do something with info events
            try:
                info_code = event['code']
            except KeyError:
                info_code = None
            if info_code:
                pass
        elif event_type == 'subscribed':
            channel_id = event['chanId'] # int
            channel_symbol = event['symbol']
            self._channel_symbols[channel_id] = channel_symbol
            self.books[channel_symbol] = {
                                          'bid': {},
                                          'ask': {}
                                         }
    @staticmethod
    def get_channel_id(data):
        """ Channel id is always the first element in snapshot/update list """
        assert isinstance(data, list)
        assert len(data) > 1
        return data[0]

    @staticmethod
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

    @staticmethod
    def update_order_book(book, stream_fields):
        try:
            for stream_field in stream_fields:
                assert len(stream_field) is 3
                price, count, amount  = stream_field
                # delete price level
                if count == 0:
                    if amount == NO_ASKS_AT_LEVEL:
                        del book['ask'][price]
                    elif amount == NO_BIDS_AT_LEVEL:
                        del book['bid'][price]
                else:
                    if amount > 0:
                        book['bid'][price] = amount
                    elif amount < 0:
                        amount = abs(amount) # easier to work with just positive mount
                        book['ask'][price] = amount
        except TypeError:
            pass
        return book

    @staticmethod
    def is_heartbeat(data):
        assert len(data) > 1
        if isinstance(data[1], str) and data[1] == 'hb':
            return True
        else:
            return False

    def handle_data(self, data):
        """ Handle book snapshot or update"""
        if not BitfinexOrderBookWS.is_heartbeat(data):
            channel_id = BitfinexOrderBookWS.get_channel_id(data)
            symbol = self._channel_symbols[channel_id]
            book = self.books[symbol]
            stream_fields = BitfinexOrderBookWS.get_stream_fields(data)
            book = BitfinexOrderBookWS.update_order_book(book, stream_fields)
            self.books[symbol] = book

if __name__ == '__main__':
    # for testing the module
    import threading
    import time

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
    while True:
        print(book_conn.books)
        print(book_conn._channel_symbols)
        time.sleep(5)
