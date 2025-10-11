import os
import django
import requests
from exchange.models import Exchange

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'multy_trader.settings')
django.setup()


class PriceChecker:
    def __init__(self, **kwargs):
        self.wallet_pair = kwargs.get('wallet_pair')
        self.base_url = kwargs.get('base_url')
        self.api_endpoint = kwargs.get('api_endpoint')
        self.exchange_type = kwargs.get('exchange_type')  # 'mexc' или 'gate'
        self.trade_type = kwargs.get('trade_type') 
        #self.order = kwargs.get('order')
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def get_ticker(self):
        """
        Получить тикер для пары
        """
        url = f"{self.base_url}{self.api_endpoint}"

        # Параметры в зависимости от биржи
        if self.exchange_type is None:
            return None
        elif self.exchange_type == 'mexc':
            params = {'symbol': self.wallet_pair if self.wallet_pair else "BTCUSDT"}
        elif self.exchange_type == 'gate':
            params = {'currency_pair': self.wallet_pair if self.wallet_pair else "BTC_USDT"}
        elif self.exchange_type == 'bybit': #"/v5/market/tickers" api endpoint
            params = {
                'category': 'spot',  # для спот торговли
                'symbol': self.wallet_pair if self.wallet_pair else "BTCUSDT"
            }
        else:
            params = {}

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Ошибка запроса: {e}")
            return None

    def get_order_book(self, limit=2):
        """
        Получить стакан цен (order book)
        limit: количество уровней в стакане
        """
        if self.exchange_type == 'mexc':
            # MEXC API для стакана
            endpoint = "/api/v3/depth"
            params = {
                'symbol': self.wallet_pair if self.wallet_pair else "BTCUSDT",
                'limit': limit
            }
        elif self.exchange_type == 'gate':
            # Gate.io API для стакана
            endpoint = "/api/v4/spot/order_book"
            params = {
                'currency_pair': self.wallet_pair if self.wallet_pair else "BTC_USDT",
                'limit': limit
            }
        elif self.exchange_type == 'bybit':
            # Bybit API для фьючерсов
            endpoint = "/v5/market/orderbook"
            params = {
                'category': 'linear',  # 'linear' для USDT-фьючерсов, 'inverse' для инверсных
                'symbol': self.wallet_pair if self.wallet_pair else "BTCUSDT",
                'limit': limit
            }
        else:
            return None

        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка получения стакана: {e}")
            return None

    def get_bid_ask_prices(self, limit=1):
        """
        Получить лучшие цены покупки (bid) и продажи (ask)
        """
        order_book = self.get_order_book(limit)
        if not order_book:
            return None
        if self.exchange_type == 'mexc':
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            best_bid = float(bids[0][0]) if bids else None  # Первый элемент в bids - лучшая цена покупки
            best_ask = float(asks[0][0]) if asks else None  # Первый элемент в asks - лучшая цена продажи

        if self.exchange_type == 'gate':
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            best_bid = float(bids[0][0]) if bids else None  # Первый элемент в bids - лучшая цена покупки
            best_ask = float(asks[0][0]) if asks else None  # Первый элемент в asks - лучшая цена продажи

        if self.exchange_type == 'bybit':
            bids = order_book.get("result").get('b', [])  # Bybit использует 'b' для bids
            asks = order_book.get("result").get('a', [])  # Bybit использует 'a' для asks
            best_bid = float(bids[0][0]) if bids else None
            best_ask = float(asks[0][0]) if asks else None

        if self.trade_type == "LONG":
            return {
                'best_bid': best_bid
            }

        elif self.trade_type == "SHORT":
            return {
                'best_ask': best_ask
            }
        return {
            'best_bid': best_bid,  # Лучшая цена покупки (максимальная цена, по которой хотят купить)
            'best_ask': best_ask,  # Лучшая цена продажи (минимальная цена, по которой хотят продать)
            # 'spread': best_ask - best_bid if best_bid and best_ask else None,  # Спред
            # 'spread_percent': ((best_ask - best_bid) / best_bid * 100) if best_bid and best_ask else None
        }

    def get_price(self):
        """Получить текущую цену"""
        ticker = self.get_ticker()

        if ticker is None:
            return None

        if self.exchange_type == 'mexc':
            return {
                'price': float(ticker['lastPrice']),
                'high': float(ticker['highPrice']),
                'low': float(ticker['lowPrice']),
                'volume': float(ticker['volume']),
                'change': float(ticker['priceChangePercent']),
            }
        elif self.exchange_type == 'gate':
            # Gate.io возвращает список с одним элементом
            if isinstance(ticker, list) and len(ticker) > 0:
                ticker_data = ticker[0]
                return {
                    'price': float(ticker_data['last']),
                    'high': float(ticker_data['high_24h']),
                    'low': float(ticker_data['low_24h']),
                    'volume': float(ticker_data['quote_volume']),
                    'change': float(ticker_data['change_percentage']),
                }
        elif self.exchange_type == 'bybit':
                # Bybit возвращает данные в отдельном объекте
            return {
                'price': float(ticker.get('lastPrice', 0)),
                'high': float(ticker.get('highPrice24h', 0)),
                'low': float(ticker.get('lowPrice24h', 0)),
                'volume': float(ticker.get('volume24h', 0)),
                'change': float(ticker.get('price24hPcnt', 0)) * 100,  # Конвертируем в проценты
            }
        return None

    def get_full_market_data(self, limit=10):
        """
        Получить полные рыночные данные: текущую цену + стакан
        """
        price_data = self.get_price()
        bid_ask_data = self.get_bid_ask_prices(limit)

        if price_data and bid_ask_data:
            return {**price_data, **bid_ask_data}
        elif price_data:
            return price_data
        elif bid_ask_data:
            return bid_ask_data
        else:
            return None


def get_wallet_pair(wallet_pair, exchange) -> str:
    """Достает имя валютной пары привязанное к нужной бирже"""

    all_wallet = wallet_pair.exchange_mappings.all()
    for local_exchange_wallet in all_wallet:
        if local_exchange_wallet.exchange == Exchange.objects.get(name=exchange):
            return local_exchange_wallet.local_name


class PriceCheckerFactory():
    @staticmethod
    def create_price_checker(wallet_pair, order):
        exchange = order.exchange_account.exchange
        return PriceChecker(
            wallet_pair=wallet_pair,
            base_url=exchange.base_url,
            api_endpoint=exchange.api_endpoint,
            exchange_type=exchange.name.lower(),
            trade_type = order.trade_type
        )