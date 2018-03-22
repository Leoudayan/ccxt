# -*- coding: utf-8 -*-

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

from ccxt.base.exchange import Exchange
import json
from ccxt.base.errors import ExchangeError
from ccxt.base.errors import AuthenticationError
from ccxt.base.errors import OrderNotFound
from ccxt.base.errors import DDoSProtection


class bitmex (Exchange):

    def describe(self):
        return self.deep_extend(super(bitmex, self).describe(), {
            'id': 'bitmex',
            'name': 'BitMEX',
            'countries': 'SC',  # Seychelles
            'version': 'v1',
            'userAgent': None,
            'rateLimit': 2000,
            'has': {
                'CORS': False,
                'fetchOHLCV': True,
                'withdraw': True,
                'editOrder': True,
                'fetchOrder': True,
                'fetchOrders': True,
                'fetchOpenOrders': True,
                'fetchClosedOrders': True,
            },
            'timeframes': {
                '1m': '1m',
                '5m': '5m',
                '1h': '1h',
                '1d': '1d',
            },
            'urls': {
                'test': 'https://testnet.bitmex.com',
                'logo': 'https://user-images.githubusercontent.com/1294454/27766319-f653c6e6-5ed4-11e7-933d-f0bc3699ae8f.jpg',
                'api': 'https://www.bitmex.com',
                'www': 'https://www.bitmex.com',
                'doc': [
                    'https://www.bitmex.com/app/apiOverview',
                    'https://github.com/BitMEX/api-connectors/tree/master/official-http',
                ],
            },
            'api': {
                'public': {
                    'get': [
                        'announcement',
                        'announcement/urgent',
                        'funding',
                        'instrument',
                        'instrument/active',
                        'instrument/activeAndIndices',
                        'instrument/activeIntervals',
                        'instrument/compositeIndex',
                        'instrument/indices',
                        'insurance',
                        'leaderboard',
                        'liquidation',
                        'orderBook',
                        'orderBook/L2',
                        'quote',
                        'quote/bucketed',
                        'schema',
                        'schema/websocketHelp',
                        'settlement',
                        'stats',
                        'stats/history',
                        'trade',
                        'trade/bucketed',
                    ],
                },
                'private': {
                    'get': [
                        'apiKey',
                        'chat',
                        'chat/channels',
                        'chat/connected',
                        'execution',
                        'execution/tradeHistory',
                        'notification',
                        'order',
                        'position',
                        'user',
                        'user/affiliateStatus',
                        'user/checkReferralCode',
                        'user/commission',
                        'user/depositAddress',
                        'user/margin',
                        'user/minWithdrawalFee',
                        'user/wallet',
                        'user/walletHistory',
                        'user/walletSummary',
                    ],
                    'post': [
                        'apiKey',
                        'apiKey/disable',
                        'apiKey/enable',
                        'chat',
                        'order',
                        'order/bulk',
                        'order/cancelAllAfter',
                        'order/closePosition',
                        'position/isolate',
                        'position/leverage',
                        'position/riskLimit',
                        'position/transferMargin',
                        'user/cancelWithdrawal',
                        'user/confirmEmail',
                        'user/confirmEnableTFA',
                        'user/confirmWithdrawal',
                        'user/disableTFA',
                        'user/logout',
                        'user/logoutAll',
                        'user/preferences',
                        'user/requestEnableTFA',
                        'user/requestWithdrawal',
                    ],
                    'put': [
                        'order',
                        'order/bulk',
                        'user',
                    ],
                    'delete': [
                        'apiKey',
                        'order',
                        'order/all',
                    ],
                },
            },
        })

    def fetch_markets(self):
        markets = self.publicGetInstrumentActiveAndIndices()
        result = []
        for p in range(0, len(markets)):
            market = markets[p]
            active = (market['state'] != 'Unlisted')
            id = market['symbol']
            base = market['underlying']
            quote = market['quoteCurrency']
            type = None
            future = False
            prediction = False
            basequote = base + quote
            base = self.common_currency_code(base)
            quote = self.common_currency_code(quote)
            swap = (id == basequote)
            symbol = id
            if swap:
                type = 'swap'
                symbol = base + '/' + quote
            elif id.find('B_') >= 0:
                prediction = True
                type = 'prediction'
            else:
                future = True
                type = 'future'
            maker = market['makerFee']
            taker = market['takerFee']
            result.append({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'active': active,
                'taker': taker,
                'maker': maker,
                'type': type,
                'spot': False,
                'swap': swap,
                'future': future,
                'prediction': prediction,
                'info': market,
            })
        return result

    def fetch_balance(self, params={}):
        self.load_markets()
        response = self.privateGetUserMargin({'currency': 'all'})
        result = {'info': response}
        for b in range(0, len(response)):
            balance = response[b]
            currency = balance['currency'].upper()
            currency = self.common_currency_code(currency)
            account = {
                'free': balance['availableMargin'],
                'used': 0.0,
                'total': balance['marginBalance'],
            }
            if currency == 'BTC':
                account['free'] = account['free'] * 0.00000001
                account['total'] = account['total'] * 0.00000001
            account['used'] = account['total'] - account['free']
            result[currency] = account
        return self.parse_balance(result)

    def fetch_order_book(self, symbol, limit=None, params={}):
        self.load_markets()
        orderbook = self.publicGetOrderBookL2(self.extend({
            'symbol': self.market_id(symbol),
        }, params))
        timestamp = self.milliseconds()
        result = {
            'bids': [],
            'asks': [],
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
        }
        for o in range(0, len(orderbook)):
            order = orderbook[o]
            side = 'asks' if (order['side'] == 'Sell') else 'bids'
            amount = order['size']
            price = order['price']
            result[side].append([price, amount])
        result['bids'] = self.sort_by(result['bids'], 0, True)
        result['asks'] = self.sort_by(result['asks'], 0)
        return result

    def fetch_order(self, id, symbol=None, params={}):
        filter = {'filter': {'orderID': id}}
        result = self.fetch_orders(symbol, None, None, self.deep_extend(filter, params))
        numResults = len(result)
        if numResults == 1:
            return result[0]
        raise OrderNotFound(self.id + ': The order ' + id + ' not found.')

    def fetch_orders(self, symbol=None, since=None, limit=None, params={}):
        self.load_markets()
        market = None
        request = {}
        if symbol is not None:
            market = self.market(symbol)
            request['symbol'] = market['id']
        if since is not None:
            request['startTime'] = self.iso8601(since)
        if limit is not None:
            request['count'] = limit
        request = self.deep_extend(request, params)
        # why the hassle? urlencode in python is kinda broken for nested dicts.
        # E.g. self.urlencode({"filter": {"open": True}}) will return "filter={'open':+True}"
        # Bitmex doesn't like that. Hence resorting to self hack.
        if 'filter' in request:
            request['filter'] = self.json(request['filter'])
        response = self.privateGetOrder(request)
        return self.parse_orders(response, market, since, limit)

    def fetch_open_orders(self, symbol=None, since=None, limit=None, params={}):
        filter_params = {'filter': {'open': True}}
        return self.fetch_orders(symbol, since, limit, self.deep_extend(filter_params, params))

    def fetch_closed_orders(self, symbol=None, since=None, limit=None, params={}):
        # Bitmex barfs if you set 'open': False in the filter...
        orders = self.fetch_orders(symbol, since, limit, params)
        return self.filter_by(orders, 'status', 'closed')

    def fetch_ticker(self, symbol, params={}):
        self.load_markets()
        market = self.market(symbol)
        if not market['active']:
            raise ExchangeError(self.id + ': symbol ' + symbol + ' is delisted')
        request = self.extend({
            'symbol': market['id'],
            'binSize': '1d',
            'partial': True,
            'count': 1,
            'reverse': True,
        }, params)
        quotes = self.publicGetQuoteBucketed(request)
        quotesLength = len(quotes)
        quote = quotes[quotesLength - 1]
        tickers = self.publicGetTradeBucketed(request)
        ticker = tickers[0]
        timestamp = self.milliseconds()
        open = self.safe_float(ticker, 'open')
        close = self.safe_float(ticker, 'close')
        change = close - open
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': float(ticker['high']),
            'low': float(ticker['low']),
            'bid': float(quote['bidPrice']),
            'bidVolume': None,
            'ask': float(quote['askPrice']),
            'askVolume': None,
            'vwap': float(ticker['vwap']),
            'open': open,
            'close': close,
            'last': close,
            'previousClose': None,
            'change': change,
            'percentage': change / open * 100,
            'average': self.sum(open, close) / 2,
            'baseVolume': float(ticker['homeNotional']),
            'quoteVolume': float(ticker['foreignNotional']),
            'info': ticker,
        }

    def parse_ohlcv(self, ohlcv, market=None, timeframe='1m', since=None, limit=None):
        timestamp = self.parse8601(ohlcv['timestamp'])
        return [
            timestamp,
            ohlcv['open'],
            ohlcv['high'],
            ohlcv['low'],
            ohlcv['close'],
            ohlcv['volume'],
        ]

    def fetch_ohlcv(self, symbol, timeframe='1m', since=None, limit=100, params={}):
        self.load_markets()
        # send JSON key/value pairs, such as {"key": "value"}
        # filter by individual fields and do advanced queries on timestamps
        # filter = {'key': 'value'}
        # send a bare series(e.g. XBU) to nearest expiring contract in that series
        # you can also send a timeframe, e.g. XBU:monthly
        # timeframes: daily, weekly, monthly, quarterly, and biquarterly
        market = self.market(symbol)
        request = {
            'symbol': market['id'],
            'binSize': self.timeframes[timeframe],
            'partial': True,     # True == include yet-incomplete current bins
            'count': limit,      # default 100, max 500
            # 'filter': filter,  # filter by individual fields and do advanced queries
            # 'columns': [],    # will return all columns if omitted
            # 'start': 0,       # starting point for results(wtf?)
            # 'reverse': False,  # True == newest first
            # 'endTime': '',    # ending date filter for results
        }
        # if since is not set, they will return candles starting from 2017-01-01
        if since is not None:
            ymdhms = self.ymdhms(since)
            ymdhm = ymdhms[0:16]
            request['startTime'] = ymdhm  # starting date filter for results
        response = self.publicGetTradeBucketed(self.extend(request, params))
        return self.parse_ohlcvs(response, market, timeframe, since, limit)

    def parse_trade(self, trade, market=None):
        timestamp = self.parse8601(trade['timestamp'])
        symbol = None
        if not market:
            if 'symbol' in trade:
                market = self.markets_by_id[trade['symbol']]
        if market:
            symbol = market['symbol']
        return {
            'id': trade['trdMatchID'],
            'info': trade,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': symbol,
            'order': None,
            'type': None,
            'side': trade['side'].lower(),
            'price': trade['price'],
            'amount': trade['size'],
        }

    def parse_order_status(self, status):
        statuses = {
            'new': 'open',
            'partiallyfilled': 'open',
            'filled': 'closed',
            'canceled': 'canceled',
            'rejected': 'rejected',
            'expired': 'expired',
        }
        return self.safe_string(statuses, status.lower())

    def parse_order(self, order, market=None):
        status = self.safe_value(order, 'ordStatus')
        if status is not None:
            status = self.parse_order_status(status)
        symbol = None
        if market:
            symbol = market['symbol']
        else:
            id = order['symbol']
            if id in self.markets_by_id:
                market = self.markets_by_id[id]
                symbol = market['symbol']
        datetime_value = None
        timestamp = None
        iso8601 = None
        if 'timestamp' in order:
            datetime_value = order['timestamp']
        elif 'transactTime' in order:
            datetime_value = order['transactTime']
        if datetime_value is not None:
            timestamp = self.parse8601(datetime_value)
            iso8601 = self.iso8601(timestamp)
        price = self.safe_float(order, 'price')
        amount = float(order['orderQty'])
        filled = self.safe_float(order, 'cumQty', 0.0)
        remaining = max(amount - filled, 0.0)
        cost = None
        if price is not None:
            if filled is not None:
                cost = price * filled
        result = {
            'info': order,
            'id': str(order['orderID']),
            'timestamp': timestamp,
            'datetime': iso8601,
            'symbol': symbol,
            'type': order['ordType'].lower(),
            'side': order['side'].lower(),
            'price': price,
            'amount': amount,
            'cost': cost,
            'filled': filled,
            'remaining': remaining,
            'status': status,
            'fee': None,
        }
        return result

    def fetch_trades(self, symbol, since=None, limit=None, params={}):
        self.load_markets()
        market = self.market(symbol)
        request = {
            'symbol': market['id'],
        }
        if since is not None:
            request['startTime'] = self.iso8601(since)
        if limit is not None:
            request['count'] = limit
        response = self.publicGetTrade(self.extend(request, params))
        return self.parse_trades(response, market)

    def create_order(self, symbol, type, side, amount, price=None, params={}):
        self.load_markets()
        request = {
            'symbol': self.market_id(symbol),
            'side': self.capitalize(side),
            'orderQty': amount,
            'ordType': self.capitalize(type),
        }
        if type == 'limit':
            request['price'] = price
        response = self.privatePostOrder(self.extend(request, params))
        order = self.parse_order(response)
        id = order['id']
        self.orders[id] = order
        return self.extend({'info': response}, order)

    def edit_order(self, id, symbol, type, side, amount=None, price=None, params={}):
        self.load_markets()
        request = {
            'orderID': id,
        }
        if amount is not None:
            request['orderQty'] = amount
        if price is not None:
            request['price'] = price
        response = self.privatePutOrder(self.extend(request, params))
        order = self.parse_order(response)
        self.orders[order['id']] = order
        return self.extend({'info': response}, order)

    def cancel_order(self, id, symbol=None, params={}):
        self.load_markets()
        response = self.privateDeleteOrder(self.extend({'orderID': id}, params))
        order = response[0]
        error = self.safe_string(order, 'error')
        if error is not None:
            if error.find('Unable to cancel order due to existing state') >= 0:
                raise OrderNotFound(self.id + ' cancelOrder() failed: ' + error)
        order = self.parse_order(order)
        self.orders[order['id']] = order
        return self.extend({'info': response}, order)

    def is_fiat(self, currency):
        if currency == 'EUR':
            return True
        if currency == 'PLN':
            return True
        return False

    def withdraw(self, currency, amount, address, tag=None, params={}):
        self.check_address(address)
        self.load_markets()
        if currency != 'BTC':
            raise ExchangeError(self.id + ' supoprts BTC withdrawals only, other currencies coming soon...')
        request = {
            'currency': 'XBt',  # temporarily
            'amount': amount,
            'address': address,
            # 'otpToken': '123456',  # requires if two-factor auth(OTP) is enabled
            # 'fee': 0.001,  # bitcoin network fee
        }
        response = self.privatePostUserRequestWithdrawal(self.extend(request, params))
        return {
            'info': response,
            'id': response['transactID'],
        }

    def handle_errors(self, code, reason, url, method, headers, body):
        if code == 429:
            raise DDoSProtection(self.id + ' ' + body)
        if code >= 400:
            if body:
                if body[0] == '{':
                    response = json.loads(body)
                    if 'error' in response:
                        if 'message' in response['error']:
                            message = self.safe_value(response['error'], 'message')
                            if message is not None:
                                if message == 'Invalid API Key.':
                                    raise AuthenticationError(self.id + ' ' + self.json(response))
                            # stub code, need proper handling
                            raise ExchangeError(self.id + ' ' + self.json(response))

    def nonce(self):
        return self.milliseconds()

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        query = '/api' + '/' + self.version + '/' + path
        if method != 'PUT':
            if params:
                query += '?' + self.urlencode(params)
        url = self.urls['api'] + query
        if api == 'private':
            self.check_required_credentials()
            nonce = str(self.nonce())
            auth = method + query + nonce
            if method == 'POST' or method == 'PUT':
                if params:
                    body = self.json(params)
                    auth += body
            headers = {
                'Content-Type': 'application/json',
                'api-nonce': nonce,
                'api-key': self.apiKey,
                'api-signature': self.hmac(self.encode(auth), self.encode(self.secret)),
            }
        return {'url': url, 'method': method, 'body': body, 'headers': headers}
