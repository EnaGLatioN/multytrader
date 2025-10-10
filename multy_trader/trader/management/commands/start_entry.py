import time
import logging
from django.core.management.base import BaseCommand

from utils import PriceChecker, PriceCheckerFacktory
from trade.models import Entry
from exchange.models import Exchange
from trade.services import gate_services, mexc_services, bybit_services, services


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--entry_id',  type=str, nargs='?', help='id входа ордера')

    def handle(self, *args, **options):
        self.start_buy(options.get("entry_id", None))

    def futures_buy(self, price_checker_long, price_checker_short, long_order, short_order, entry, flag, status):
        logger.info('-------STATUS------')
        logger.info(status)
        while flag:
            time.sleep(1)
            bid = price_checker_long.get_bid_ask_prices()
            ask = price_checker_short.get_bid_ask_prices()
            getter_course = ((bid.get("best_bid") / ask.get("best_ask")) - 1) * 100
            if status == "WAIT":
                
                logger.info('-------STATUS------')
                logger.info(status)
                logger.info('-------entry.entry_course------')
                logger.info(entry.entry_course)

                if getter_course <= entry.entry_course:
                    continue

                self.long_buy(long_order, entry)
                self.short_buy(short_order, entry)

                self.update_status_entry(entry, "ACTIVE")
                flag = False
            elif status == "ACTIVE":
                exit_course = entry.exit_course
                if entry.exit_course:
                    if getter_course >= exit_course:
                        continue
                    self.long_buy(long_order, entry)
                    self.short_buy(short_order, entry)

                    self.update_status_entry(entry, "COMPLETED")

                    flag = False


    def start_buy(self, entry_id):

        entry = self.get_entry(entry_id)

        orders = entry.order_entry.all()
        long_order = None
        short_order = None
        flag = True
        for order in orders:
            exchange_type = order.exchange_account.exchange.name
            wallet_pair = self.get_wallet_pair(entry.wallet_pair, exchange_type)

            if order.trade_type == "LONG":
                long_order = order
                price_checker_long = PriceCheckerFacktory.create_price_checker(wallet_pair, order)
            else:
                short_order = order
                price_checker_short = PriceCheckerFacktory.create_price_checker(wallet_pair, order)

        self.futures_buy(price_checker_long, price_checker_short, long_order, short_order, entry, flag, entry.status)
        
        long_order.trade_type = "SHORT"
        short_order.trade_type = "LONG"

        self.futures_buy(price_checker_long, price_checker_short, long_order, short_order, entry, flag, entry.status)


    def get_entry(self, entry_id):
        try:
            return Entry.objects.get(id=entry_id)
        except Entry.DoesNotExist:
            raise Entry.DoesNotExist

    def update_status_entry(self, entry, status):
        """Обновляет статус входа"""

        entry.status = status
        entry.save()

    def long_buy(self, long_order, entry):
        exchange_name = long_order.exchange_account.exchange.name
        if exchange_name == 'gate':
            gate_services.gate_buy_futures_contract(entry, long_order)
        if exchange_name == 'mexc':
            mexc_services.mexc_buy_futures_contract(entry, long_order)
        if exchange_name == 'bybit':
            bybit_services.bybit_buy_futures_contract(entry, long_order)

    def short_buy(self, short_order, entry):
        exchange_name = short_order.exchange_account.exchange.name
        if exchange_name == 'gate':
            gate_services.gate_buy_futures_contract(entry, short_order)
        if exchange_name == 'mexc':
            mexc_services.gate_buy_futures_contract(entry, short_order)
        if exchange_name == 'bybit':
            bybit_services.gate_buy_futures_contract(entry, short_order)

    def get_wallet_pair(self, wallet_pair, exchange) -> str:
        """Достает имя валютной пары привязанное к нужной бирже"""

        all_wallet = wallet_pair.exchange_mappings.all()
        for local_exchange_wallet in all_wallet:
            if local_exchange_wallet.exchange == Exchange.objects.get(name=exchange):
                return local_exchange_wallet.local_name
