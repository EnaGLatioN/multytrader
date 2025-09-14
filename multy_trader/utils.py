import os
import django
import requests
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'multy_trader.settings')
django.setup()


class PriceChecker:
    def __init__(self, base_url, api_endpoint, wallet_pair=None, exchange_type=None):
        self.wallet_pair = wallet_pair
        self.base_url = base_url
        self.api_endpoint = api_endpoint
        self.exchange_type = exchange_type  # 'mexc' или 'gate'
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
            local_name = self.get_wallet_pair_mexc(self.wallet_pair)
            params = {'symbol': local_name if local_name else "BTCUSDT"}
        elif self.exchange_type == 'gate':
            local_name = self.get_wallet_pair_gate(self.wallet_pair)
            params = {'currency_pair': local_name if local_name else "BTC_USDT"}
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

    def get_bid_ask_prices(self, limit=2, buy_type=None):
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

        if buy_type == "LONG":
            return {
                'best_bid': best_bid
            }
        if buy_type == "SHORT":
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

    def get_wallet_pair_gate(self, wallet_pair):
        all_wallet = wallet_pair.exchange_mappings
        exchange = Exchange.objects.get(name='GATE')
        for i in all_wallet:
            if i.exchange == exchange:
                return i.local_name

    def get_wallet_pair_mexc(self, wallet_pair):
        all_wallet = wallet_pair.exchange_mappings
        exchange = Exchange.objects.get(name='MEXC')
        for i in all_wallet:
            if i.exchange == exchange:
                return i.local_name

# if __name__ == "__main__":
#     print("MEXC Market Data:")
#     mexc_checker = PriceChecker(
#         wallet_pair="BTCUSDT",
#         base_url=settings.BASE_URL_MEXC,
#         api_endpoint=settings.API_ENDPOINT_MEXC,
#         exchange_type='mexc'
#     )
#
#     # Получаем полные данные
#     mexc_data = mexc_checker.get_full_market_data()
#     print("Текущая цена:", mexc_data.get('price'))
#     print("Лучшая цена покупки (bid):", mexc_data.get('best_bid'))
#     print("Лучшая цена продажи (ask):", mexc_data.get('best_ask'))
#     print("Спред:", mexc_data.get('spread'))
#     print("Спред (%):", f"{mexc_data.get('spread_percent', 0):.4f}%")
#
#     print("\n" + "=" * 50 + "\n")
#
#     print("Gate.io Market Data:")
#     gate_checker = PriceChecker(
#         wallet_pair="BTC_USDT",
#         base_url=settings.BASE_URL_GATE,
#         api_endpoint=settings.API_ENDPOINT_GATE,
#         exchange_type='gate'
#     )
#
#     # Получаем только стакан
#     gate_bid_ask = gate_checker.get_bid_ask_prices()
#     print("Лучшая цена покупки (bid):", gate_bid_ask.get('best_bid'))
#     print("Лучшая цена продажи (ask):", gate_bid_ask.get('best_ask'))
#     print("Спред:", gate_bid_ask.get('spread'))
#     print("Спред (%):", f"{gate_bid_ask.get('spread_percent', 0):.4f}%")
#
#     # Можно также получить полные данные
#     gate_full_data = gate_checker.get_full_market_data()
#     print("Текущая цена:", gate_full_data.get('price'))