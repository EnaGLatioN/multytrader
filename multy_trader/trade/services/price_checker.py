import os
from typing import Any

import django
import requests
from exchange.models import Exchange


class PriceChecker:
    def __init__(self, **kwargs):
        self.wallet_pair = kwargs.get('wallet_pair')
        self.base_url = kwargs.get('base_url')
        self.api_endpoint = kwargs.get('api_endpoint')
        self.exchange_type = kwargs.get('exchange_type')
        self.trade_type = kwargs.get('trade_type') 
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })

    def get_order_book(self, limit=2):
        """
        Получить стакан цен (order book)
        limit: количество уровней в стакане
        """
        
        if self.exchange_type == 'mexc':
            # MEXC API для стакана
            endpoint = "/api/v3/depth"
            params = {
                'symbol': self.wallet_pair if self.wallet_pair else None,
                'limit': limit
            }
        elif self.exchange_type == 'gate':
            # Gate.io API для стакана
            endpoint = "/api/v4/futures/usdt/order_book"
            params = {
                'contract': self.wallet_pair if self.wallet_pair else None,
                'limit': limit
            }
        elif self.exchange_type == 'bybit':
            # Bybit API для фьючерсов
            endpoint = "/v5/market/orderbook"
            params = {
                'category': 'linear',  # 'linear' для USDT-фьючерсов, 'inverse' для инверсных
                'symbol': self.wallet_pair if self.wallet_pair else None,
                'limit': limit
            }
        elif self.exchange_type == 'kucoin':
            endpoint = "/api/v1/level2/snapshot"
            params = {
                'symbol': self.wallet_pair if self.wallet_pair else None
            }
        elif self.exchange_type == 'okx':
            endpoint = '/api/v5/market/books'
            params = {
                'instId': self.wallet_pair if self.wallet_pair else None,
                'sz': limit
            }
        elif self.exchange_type == 'ourbit':
            endpoint = f'/api/v1/contract/depth_step/{self.wallet_pair}'
            params = {}
        elif self.exchange_type == 'htx':
            endpoint = '/linear-swap-ex/market/depth'
            params = {
                'contract_code': self.wallet_pair if self.wallet_pair else None,
                'type': 'step0'
            }
        elif self.exchange_type == 'bingx':
            endpoint = '/openApi/swap/v2/quote/depth'
            params = {
                'symbol': self.wallet_pair if self.wallet_pair else None
            }
        elif self.exchange_type == 'binance':
            endpoint = '/fapi/v1/depth'
            params = {
                'symbol': self.wallet_pair if self.wallet_pair else None,
                'limit': 5
            }
        else:
            return None

        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=10, verify=False)
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

        elif self.exchange_type == 'gate':
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            best_bid = float(bids[0]['p']) if bids else None  # Первый элемент в bids - лучшая цена покупки
            best_ask = float(asks[0]['p']) if asks else None  # Первый элемент в asks - лучшая цена продажи

        elif self.exchange_type == 'kucoin':
            bids = order_book.get("data").get('bids', [])
            asks = order_book.get("data").get('asks', [])
            best_bid = float(bids[0][0]) if bids else None
            best_ask = float(asks[0][0]) if asks else None

        elif self.exchange_type == 'bybit':
            bids = order_book.get("result").get('b', [])  # Bybit использует 'b' для bids
            asks = order_book.get("result").get('a', [])  # Bybit использует 'a' для asks
            best_bid = float(bids[0][0]) if bids else None
            best_ask = float(asks[0][0]) if asks else None
        
        elif self.exchange_type == 'okx':
            bids = order_book.get("data")[0].get('bids', [])
            asks = order_book.get("data")[0].get('asks', [])
            best_bid = float(bids[0][0]) if bids else None
            best_ask = float(asks[0][0]) if asks else None

        elif self.exchange_type == 'ourbit':
            bids = order_book.get("data").get('bids', [])
            asks = order_book.get("data").get('asks', [])
            best_bid = float(bids[0][0]) if bids else None
            best_ask = float(asks[0][0]) if asks else None
        
        elif self.exchange_type == 'htx':
            bids = order_book.get("tick").get('bids', [])
            asks = order_book.get("tick").get('asks', [])
            best_bid = float(bids[0][0]) if bids else None
            best_ask = float(asks[0][0]) if asks else None
        
        elif self.exchange_type == 'bingx':
            bids = order_book.get("data").get('bids', [])
            asks = order_book.get("data").get('asks', [])
            best_bid = float(bids[0][0]) if bids else None
            best_ask = float(asks[0][0]) if asks else None
        
        elif self.exchange_type == 'binance':
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            best_bid = float(bids[0][0]) if bids else None
            best_ask = float(asks[0][0]) if asks else None

        return {
            'best_bid': best_bid,  # Лучшая цена покупки (максимальная цена, по которой хотят купить)
            'best_ask': best_ask,  # Лучшая цена продажи (минимальная цена, по которой хотят продать)
            # 'spread': best_ask - best_bid if best_bid and best_ask else None,  # Спред
            # 'spread_percent': ((best_ask - best_bid) / best_bid * 100) if best_bid and best_ask else None
        }


class PriceCheckerFactory():
    @staticmethod
    def create_price_checker(wallet_pair, order):
        exchange = order.exchange_account.exchange
        return PriceChecker(
            wallet_pair=wallet_pair,
            base_url=exchange.base_url,
            api_endpoint=exchange.api_endpoint,
            exchange_type=exchange.name.lower()
        )
        