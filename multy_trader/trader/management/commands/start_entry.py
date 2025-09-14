import time
import logging
from django.core.management.base import BaseCommand

from utils import PriceChecker
from trade.models import Entry
from trade.services import gate_services, mexc_services


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--entry_id',  type=str, nargs='?', help='id входа ордера')

    def handle(self, *args, **options):
        self.start_buy(options.get("entry_id", None))

    def futures_buy(self, price_checker_long, price_checker_short, long_order, short_order, entry, flag, status):
        while flag:
            time.sleep(2)
            bid = price_checker_long.get_bid_ask_prices(long_order.trade_type)
            ask = price_checker_short.get_bid_ask_prices(short_order.trade_type)
            getter_course = ((bid.get("best_bid") / ask.get("best_ask")) - 1) * 100
            if status == "ACTIVE":
                if getter_course <= entry.entry_course:
                    continue

                mexc_services.mexc_buy_futures_contract(entry,
                                                        long_order if long_order.exchange_account.exchange.name.lower() == 'mexc' else short_order)
                gate_services.gate_buy_futures_contract(entry,
                                                        short_order if short_order.exchange_account.exchange.name.lower() == 'gate' else long_order)
                entry.status = status
                entry.save()
                flag = False
            else:
                if getter_course >= entry.exit_course:
                    continue

                mexc_services.mexc_buy_futures_contract(entry,
                                                        long_order if long_order.exchange_account.exchange.name.lower() == 'mexc' else short_order)
                gate_services.gate_buy_futures_contract(entry,
                                                        short_order if short_order.exchange_account.exchange.name.lower() == 'gate' else long_order)
                entry.status = status
                entry.save()
                flag = False

    def start_buy(self, entry_id):
        try:
            entry = Entry.objects.get(id=entry_id)
        except Entry.DoesNotExist:
            raise Entry.DoesNotExist
        orders = entry.order_entry.all()
        long_order = None
        short_order = None
        flag = True
        for order in orders:
            print('-----order-----')
            print(order)
            if order.trade_type == "LONG":
                long_order = order
                price_checker_long = PriceChecker(
                                        wallet_pair=entry.wallet_pair,
                                        base_url=order.exchange_account.exchange.base_url,
                                        api_endpoint=order.exchange_account.exchange.api_endpoint,
                                        exchange_type=order.exchange_account.exchange.name.lower()
                                    )
                print(price_checker_long)
            else:
                short_order = order
                price_checker_short = PriceChecker(
                                    wallet_pair=entry.wallet_pair,
                                    base_url=order.exchange_account.exchange.base_url,
                                    api_endpoint=order.exchange_account.exchange.api_endpoint,
                                    exchange_type = order.exchange_account.exchange.name.lower()
                                )
                print(price_checker_short)

        self.futures_buy(price_checker_long, price_checker_short, long_order, short_order, entry, flag, "ACTIVE")
        long_order.trade_type = "SHORT"
        short_order.trade_type = "LONG"
        self.futures_buy(price_checker_long, price_checker_short, long_order, short_order, entry, flag, "COMPLETED")



