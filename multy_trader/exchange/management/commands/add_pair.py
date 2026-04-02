import logging
import requests
from django.db.models import Value
from django.db.models.functions import Replace, Upper
import gate_api
from django.core.management.base import BaseCommand
from exchange.models import PairExchangeMapping, WalletPair, Exchange


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Фьючерсные контракты.

    При вставке валютных пар в модельку PairExchangeMapping,
    где хранятся локальные валютные пары с каждой биржи, также проверяем
    нормализованное название валюной пары среди имеющихся единых пар, чтобы 
    связать все локальные валютные пары в единую пару.

    Парсим минимальное количество монет у каждой валютной пары.
    """

    def handle(self, *args, **options):
        #PairExchangeMapping.objects.all().delete()
        #WalletPair.objects.all().delete()

        exchanges = {
            'GATE': self.get_wallet_pairs_from_gate,
            'BYBIT': self.get_wallet_pairs_from_bybit,
            'KUCOIN': self.get_wallet_pairs_kucoin,
            'BINANCE': self.get_wallet_pairs_binance,
            'HTX': self.get_wallet_pairs_htx, ###
            'MEXC': self.get_wallet_pairs_mexc, ###
            'BINGX': self.get_wallet_pairs_bingx,
            'OURBIT': self.get_wallet_pairs_ourbit, ###
            'OKX': self.get_wallet_pairs_okx
        }
        
        for name, func in exchanges.items():
            exchange = self.get_or_create_exchange(name)
            func(exchange)
            logger.info(f"Succes added pairs {name}")
        
        self.shibari()

    def get_or_create_exchange(self, exchange: str) -> Exchange:
        """Достает или создает биржу"""

        exchange, _ = Exchange.objects.get_or_create(name=exchange)
        return exchange

    def get_wallet_pairs_from_gate(self, exchange: Exchange) -> None:
        """
        Достает валютные пары с биржи GATE
        """

        configuration = gate_api.Configuration(
            host="https://fx-api.gateio.ws/api/v4"
        )
        api_instance = gate_api.FuturesApi(gate_api.ApiClient(configuration))
        response = api_instance.list_futures_contracts(settle='usdt')

        for resp in response:
            order_size_min = float(resp.order_size_min) if resp.order_size_min else 1
            quanto_multiplier = float(resp.quanto_multiplier) if resp.quanto_multiplier else 1
            self.create_pair_exchange_mapping(
                resp.name,
                exchange,
                min_order=order_size_min * quanto_multiplier,
                coin_count=quanto_multiplier,
                step=quanto_multiplier,
            )

    def get_wallet_pairs_from_bybit(self, exchange: Exchange) -> None:
        """
        Достает валютные пары с биржи BYBIT
        """

        url = "https://api.bybit.com/v5/market/instruments-info"
        response = requests.get(url, params={"category": "linear", "limit": 1000})
        data = response.json()

        response.raise_for_status()

        for symbol in data["result"]["list"]:
            lot = symbol['lotSizeFilter']
            self.create_pair_exchange_mapping(
                symbol['symbol'],
                exchange,
                min_order=float(lot['minOrderQty']),
                coin_count=1,
                step=float(lot['qtyStep']),
                min_notional=float(lot['minNotionalValue']) if 'minNotionalValue' in lot else None,
            )
    
    def get_wallet_pairs_kucoin(self, exchange: Exchange) -> None:
        """
        Достает валютные пары с биржи KUCOIN.
        """
        # С суффиксом USDM (без T) - старые inverse-контракты
        url = "https://api-futures.kucoin.com/api/v1/contracts/active"
        response = requests.get(url)
        data = response.json()

        response.raise_for_status()
        for symbol in data['data']:
            if symbol.get('isInverse'):
                continue
            multiplier = float(symbol['multiplier'])
            self.create_pair_exchange_mapping(
                symbol['symbol'],
                exchange,
                min_order=float(symbol['lotSize']) * multiplier,
                coin_count=multiplier,
                step=multiplier,
            )
    
    def get_wallet_pairs_binance(self, exchange: Exchange) -> None:
        """
        Достает валютные пары с биржи BINANCE.
        В Binance 1 контракт = 1 монета.
        """

        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
        response = requests.get(url)
        data = response.json()

        response.raise_for_status()
        for symbol in data['symbols']:
            lot = next((f for f in symbol['filters'] if f['filterType'] == 'LOT_SIZE'), None)
            notional_filter = next((f for f in symbol['filters'] if f['filterType'] == 'MIN_NOTIONAL'), None)
            self.create_pair_exchange_mapping(
                symbol['symbol'],
                exchange,
                min_order=float(lot['minQty']) if lot else 0,
                coin_count=1,
                step=float(lot['stepSize']) if lot else 0,
                min_notional=float(notional_filter['notional']) if notional_filter else None,
            )
    
    def get_wallet_pairs_htx(self, exchange: Exchange) -> None:
        """
        Достает валютные пары с биржи HTX.
        symbol['contract_size'] - Кол-во монет в одном контракте (например 0.001 BTC)
        """

        url = "https://api.hbdm.com/linear-swap-api/v1/swap_contract_info"
        response = requests.get(url)
        data = response.json()

        response.raise_for_status()
        for symbol in data['data']:
            contract_size = float(symbol.get('contract_size', 0))
            self.create_pair_exchange_mapping(
                symbol['contract_code'],
                exchange,
                min_order=contract_size,
                coin_count=contract_size,
                step=contract_size,
            )

    def get_wallet_pairs_mexc(self, exchange: Exchange) -> None:
        """
        Достает валютные пары с биржи MEXC.
        """

        url = "https://api.mexc.com/api/v1/contract/detail"
        response = requests.get(url)
        data = response.json()

        response.raise_for_status()
        for symbol in data['data']:
            contract_size = float(symbol.get('contractSize', 0))
            min_vol = float(symbol.get('minVol', 1))
            self.create_pair_exchange_mapping(
                symbol['symbol'],
                exchange,
                min_order=min_vol * contract_size,
                coin_count=contract_size,
                step=contract_size,
            )

    def get_wallet_pairs_bingx(self, exchange: Exchange) -> None:
        """
        Достает валютные пары с биржи BINGX.
        """

        url = "https://open-api.bingx.com/openApi/swap/v2/quote/contracts"
        response = requests.get(url)
        data = response.json()

        response.raise_for_status()
        for symbol in data['data']:
            size = float(symbol['size'])
            qty_precision = int(symbol.get('quantityPrecision', 0))
            self.create_pair_exchange_mapping(
                symbol['symbol'],
                exchange,
                min_order=float(symbol['tradeMinQuantity']),
                coin_count=size,
                step=10 ** (-qty_precision),
                min_notional=float(symbol['tradeMinUSDT']) if 'tradeMinUSDT' in symbol else None,
            )
    
    def get_wallet_pairs_ourbit(self, exchange: Exchange) -> None:
        """
        Достает валютные пары с биржи OURBIT.
        """

        url = "https://futures.ourbit.com/api/v1/contract/detail"
        response = requests.get(url)
        data = response.json()

        response.raise_for_status()
        for symbol in data['data']:
            contract_size = float(symbol.get('contractSize', 0))
            min_vol = float(symbol.get('minVol', 1))
            self.create_pair_exchange_mapping(
                symbol['symbol'],
                exchange,
                min_order=min_vol * contract_size,
                coin_count=contract_size,
                step=contract_size,
            )

    def get_wallet_pairs_okx(self, exchange: Exchange) -> None:
        """
        Достает валютные пары с биржи OKX.
        """

        url = "https://www.okx.com/api/v5/public/instruments"
    
        # Типы: SWAP (бессрочные) или FUTURES (срочные)
        params = {'instType': 'SWAP'} 
    
        response = requests.get(url, params)
        data = response.json()
    
        response.raise_for_status()
        for symbol in data['data']:
            if symbol['ctType'] == 'linear' and symbol['settleCcy'] == 'USDT':
                ct_val = float(symbol['ctVal'])
                self.create_pair_exchange_mapping(
                    symbol['instId'],
                    exchange,
                    min_order=ct_val * float(symbol['minSz']),
                    coin_count=ct_val,
                    step=ct_val * float(symbol['lotSz']),
                )

    def shibari(self):
        """
        Связываем созданные валютные пары в единую
        """
        
        pairs = PairExchangeMapping.objects.filter(wallet_pair__isnull=True)
        for pair in pairs.iterator():
            other = PairExchangeMapping.objects.filter(normalized_name=pair.normalized_name)
            if other.count() > 1:
                wallet_pair, created = WalletPair.objects.get_or_create(
                    slug=pair.normalized_name,
                    defaults={'is_active': True}
                )
        
                other.update(wallet_pair=wallet_pair)

    def create_pair_exchange_mapping(self, name: str, exchange: Exchange, **kwargs) -> None:
        """
        Создает валютные пары
        """

        PairExchangeMapping.objects.update_or_create(
            local_name=name,
            exchange=exchange,
            defaults={
                'normalized_name': self.normalyze_local_name(name),
                'min_order': kwargs.get('min_order', 0),
                'coin_count': kwargs.get('coin_count', 0),
                'step': kwargs.get('step', 0),
                'min_notional': kwargs.get('min_notional', None),
            }
        )

    def normalyze_local_name(self, name) -> str:
        """
        Нормализатор имени, приводит к верхнему регистру и удаляет мусор
        """

        clean = name.replace('_', '').replace('-', '').replace('/', '').upper()
        if clean.endswith('USDTM'):
            clean = clean[:-1]
        if clean.endswith('SWAP'):
            clean = clean[:-4]
        return clean
