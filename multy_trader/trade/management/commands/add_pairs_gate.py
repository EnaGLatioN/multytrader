import logging

import gate_api
from django.core.management.base import BaseCommand
from gate.models import WaletPairs


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.add_pairs()

    def add_pairs(self):
        configuration = gate_api.Configuration(
            host="https://api.gateio.ws/api/v4"
        )
        api_client = gate_api.ApiClient(configuration)
        api_instance = gate_api.SpotApi(api_client)
        response = api_instance.list_currency_pairs()
        for resp in response:
            WaletPairs.objects.get_or_create(
                slug=resp.id,
            )
        logger.info(f"Succes added slugs")

