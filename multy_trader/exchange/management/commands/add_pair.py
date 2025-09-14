import logging
import requests

import gate_api
from django.core.management.base import BaseCommand
from exchange.models import PairExchangeMapping, WalletPair, Exchange


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.add_pairs_gate()
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
        for symbol in data['symbols']:
            base = symbol['baseAsset']
            quote = symbol['quoteAsset']
            formatted_pair = f"{base}_{quote}"
            PairExchangeMapping.objects.get_or_create(
                local_name=formatted_pair,
                exchange=exchange
            )
        logger.info(f"Succes added slugs")
