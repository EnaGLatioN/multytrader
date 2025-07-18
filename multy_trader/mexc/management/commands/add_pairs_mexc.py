import logging
import requests

from django.core.management.base import BaseCommand
from mexc.models import WaletPairsMexc


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.add_pairs()

    def add_pairs(self):
        url = "https://api.mexc.com/api/v3/exchangeInfo"
        response = requests.get(url)
        data = response.json()
        response.raise_for_status()
        for symbol in data['symbols']:
            base = symbol['baseAsset']
            quote = symbol['quoteAsset']
            formatted_pair = f"{base}_{quote}"
            WaletPairsMexc.objects.get_or_create(
                slug=formatted_pair,
            )
        logger.info(f"Succes added slugs")


