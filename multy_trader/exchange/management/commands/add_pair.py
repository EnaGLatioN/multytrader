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
        #self.add_pairs_gate()
        self.add_pairs_mexc()

    def add_pairs_gate(self):
        configuration = gate_api.Configuration(
            host="https://api.gateio.ws/api/v4"
        )
        api_client = gate_api.ApiClient(configuration)
        api_instance = gate_api.SpotApi(api_client)
        response = api_instance.list_currency_pairs()
        exchange = Exchange.objects.get(name='GATE')
        for resp in response:
            PairExchangeMapping.objects.get_or_create(
                local_name=resp.id,
                exchange=exchange
            )
        logger.info(f"Succes added slugs")

    def add_pairs_mexc(self):
        url = "https://api.mexc.com/api/v3/exchangeInfo"
        response = requests.get(url)
        data = response.json()
        response.raise_for_status()
        exchange = Exchange.objects.get(name='MEXC')
        exchange_gate = Exchange.objects.get(name='GATE')
        for symbol in data['symbols']:
            base = symbol['baseAsset']
            quote = symbol['quoteAsset']
            formatted_pair = f"{base}_{quote}"
            
            double = self.get_double_wallet_pair(formatted_pair, exchange_gate) 
            single_wallet_pair = None

            if double:
                single_wallet_pair = WalletPair.objects.create(slug = formatted_pair)
                self.update_double_wallet_pair(double, single_wallet_pair)

            PairExchangeMapping.objects.get_or_create(
                local_name=formatted_pair,
                exchange=exchange,
                wallet_pair=single_wallet_pair
            )
        logger.info(f"Succes added slugs")
    
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

