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
        self.clear()
        self.add_pairs_gate()
        self.add_pairs_bybit()

    def clear(self):
        PairExchangeMapping.objects.all().delete()
        WalletPair.objects.all().delete()

    def add_pairs_gate(self):
        api_instance = gate_api.SpotApi(
            gate_api.ApiClient(
                gate_api.Configuration(
                    host="https://api.gateio.ws/api/v4"
                )
            )
        )
        exchange, _ = Exchange.objects.get_or_create(name='GATE')
        for resp in api_instance.list_currency_pairs():
            PairExchangeMapping.objects.get_or_create(
                local_name=resp.id,
                exchange=exchange
            )
        logger.info(f"Succes added pairs Gate")

    def add_pairs_bybit(self):
        response = requests.get(
            "https://api.bybit.com/v5/market/instruments-info",
            params = {"category": "linear"}
        )
        data = response.json()
        response.raise_for_status()
        exchange_gate, _ = Exchange.objects.get_or_create(name='GATE')
        exchange, _ = Exchange.objects.get_or_create(name='BYBIT')

        for symbol in data["result"]["list"]:
            bybit_local_name = symbol['symbol']
            double = self.get_double_wallet_pair(bybit_local_name, exchange_gate)
            single_wallet_pair = None

            if double:
                single_wallet_pair = WalletPair.objects.create(slug = double.local_name)
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
        try:
            return PairExchangeMapping.objects.annotate(
                local_name_normalized=Replace('local_name', Value('_'), Value(''))
            ).get(local_name_normalized__iexact=formatted_pair.replace('_', '').upper(), exchange = exchange_gate)
        except PairExchangeMapping.DoesNotExist:
            return None
    
    def update_double_wallet_pair(self, double, single_wallet_pair):
        double.wallet_pair = single_wallet_pair
        double.save()

