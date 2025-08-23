import logging
from django.core.management.base import BaseCommand
from multy_trader.utils import PriceChecker
from multy_trader.trade.models import Entry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--entry_id',  type=str, nargs='?', help='id входа ордера')

    def handle(self, *args, **options):
        self.start_buy(options.get("entry_id", None))

    def start_buy(self, entry_id):
        try:
            entry = Entry.objects.get(id=entry_id)
        except Entry.DoesNotExist:
            raise Entry.DoesNotExist

        PriceChecker(

        )