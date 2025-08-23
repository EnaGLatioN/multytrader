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
            params = {'symbol': self.wallet_pair if self.wallet_pair else "BTCUSDT"}
        elif self.exchange_type == 'gate':
            params = {'currency_pair': self.wallet_pair if self.wallet_pair else "BTC_USDT"}
        else:
            params = {}

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            print(f"Ошибка запроса: {e}")
            return None

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

# if __name__ == "__main__":
#     print("MEXC Price:")
#     mexc_price = PriceChecker(
#         wallet_pair="BTCUSDT",
#         base_url=settings.BASE_URL_MEXC,
#         api_endpoint=settings.API_ENDPOINT_MEXC,
#         exchange_type='mexc'
#     ).get_price()
#     print(mexc_price)
#
#     print("\nGate.io Price:")
#     gate_price = PriceChecker(
#         wallet_pair="BTC_USDT",
#         base_url=settings.BASE_URL_GATE,
#         api_endpoint=settings.API_ENDPOINT_GATE,
#         exchange_type='gate'
#     ).get_price()
#     print(gate_price)