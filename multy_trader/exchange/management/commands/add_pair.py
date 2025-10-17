import logging
import requests
from django.db.models.functions import Replace
from django.db.models import Value
import gate_api
from django.core.management.base import BaseCommand
from exchange.models import PairExchangeMapping, WalletPair, Exchange


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.add_pairs_gate()
        self.add_pairs_bybit()

    def add_pairs_gate(self):
        configuration = gate_api.Configuration(
            host="https://api.gateio.ws/api/v4"
        )
        api_instance = gate_api.FuturesApi(gate_api.ApiClient(configuration))
        response = api_instance.list_futures_contracts(settle='usdt')
        exchange, _ = Exchange.objects.get_or_create(name='GATE')
        for resp in response:
            PairExchangeMapping.objects.get_or_create(
                local_name=resp.name,
                exchange=exchange
            )
        logger.info(f"Succes added pairs Gate")

    def add_pairs_bybit(self):
        url = "https://api.bybit.com/v5/market/instruments-info"
        response = requests.get(url, params = {"category": "linear"})
        data = response.json()
        
        response.raise_for_status()
        exchange_gate, _ = Exchange.objects.get_or_create(name='GATE')
        exchange, _ = Exchange.objects.get_or_create(name='BYBIT')

        for symbol in data["result"]["list"]:
            bybit_local_name = symbol['symbol']
            double = self.get_double_wallet_pair(bybit_local_name, exchange_gate)
            single_wallet_pair = None

            if double:
                single_wallet_pair, _ = WalletPair.objects.get_or_create(slug = double.local_name)
                self.update_double_wallet_pair(double, single_wallet_pair)

            PairExchangeMapping.objects.get_or_create(
                local_name=bybit_local_name,
                exchange=exchange,
                wallet_pair=single_wallet_pair
            )
        logger.info(f"Succes added pairs ByBit")
    
    def get_double_wallet_pair(self,formatted_pair, exchange_gate):
        try:
            return PairExchangeMapping.objects.get(local_name=formatted_pair, exchange = exchange_gate)
        except PairExchangeMapping.DoesNotExist:
            return self.normalize_wallet_pair(formatted_pair, exchange_gate) 

    def normalize_wallet_pair(self, formatted_pair, exchange_gate):
        char_remove = '_'
        normalyze = formatted_pair.replace(char_remove, '').upper()

        try:
            return PairExchangeMapping.objects.annotate(
                local_name_normalized=Replace('local_name', Value('_'), Value(''))
            ).get(local_name_normalized__iexact=normalyze, exchange = exchange_gate)
        except PairExchangeMapping.DoesNotExist:
            return None
    
    def update_double_wallet_pair(self, double, single_wallet_pair):
        double.wallet_pair = single_wallet_pair
        double.save()

