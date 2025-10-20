import time
import sys
import logging
from django.core.management.base import BaseCommand

from concurrent.futures import ThreadPoolExecutor
from utils import PriceChecker, PriceCheckerFactory, get_wallet_pair
from trade.models import Entry
from exchange.models import Exchange
from trade.services import gate_services, mexc_services, bybit_services, services
from trade.bot import notification_order

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
            bid = price_checker_long.get_bid_ask_prices()
            ask = price_checker_short.get_bid_ask_prices()
            logger.info("---------BID-----------")
            logger.info(bid)
            logger.info("----------ASK---------")
            logger.info(ask)
            getter_course = (ask.get("best_bid") / (bid.get("best_ask")) - 1) * 100
            if status == "WAIT":
                
                logger.info('-------STATUS------')
                logger.info(status)
                logger.info(getter_course)

                if getter_course <= entry.entry_course:
                    continue

                with ThreadPoolExecutor(max_workers=2) as executor:
                    future_open_long = executor.submit(self.long_buy, long_order, entry)
                    future_open_short = executor.submit(self.short_buy, short_order, entry)

                result_open_long = future_open_long.result()
                result_open_short = future_open_short.result()

                # self.long_buy(long_order, entry)
                # self.short_buy(short_order, entry)
                self.check_order(result_open_long, result_open_short, entry, "OPEN")
                self.update_status_entry(entry, "ACTIVE")
                flag = False
            elif status == "ACTIVE":
                exit_course = entry.exit_course
                if entry.exit_course:
                    logger.info('-------EXIT------')
                    logger.info(getter_course)
                    if getter_course >= exit_course:
                        continue
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        result_closed_long = executor.submit(self.long_buy, long_order, entry)
                        result_closed_short = executor.submit(self.short_buy, short_order, entry)

                    result_closed_long = future_open_long.result()
                    result_closed_short = future_open_short.result()

                    # self.long_buy(long_order, entry)
                    # self.short_buy(short_order, entry)
                    self.check_order(result_closed_long, result_closed_short, entry, "CLOSED")
                    self.update_status_entry(entry, "COMPLETED")
                    flag = False

    def start_buy(self, entry_id):
        
        entry = self.get_entry(entry_id)
        
        entry.status = "WAIT"
        entry.save()

        orders = entry.order_entry.all()
        long_order = None
        short_order = None
        flag = True
        for order in orders:

            exchange_type = order.exchange_account.exchange.name
            wallet_pair = get_wallet_pair(entry.wallet_pair, exchange_type)

            if order.trade_type == "LONG":
                long_order = order
                price_checker_long = PriceCheckerFactory.create_price_checker(wallet_pair, order)
            else:
                short_order = order
                price_checker_short = PriceCheckerFactory.create_price_checker(wallet_pair, order)

        self.futures_buy(price_checker_long, price_checker_short, long_order, short_order, entry, flag, entry.status)
        
        long_order.trade_type = "SHORT"
        short_order.trade_type = "LONG"
        long_order.save()
        short_order.save()
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
        logger.info("---exchange_name long---")
        logger.info(exchange_name)
        if exchange_name == 'GATE':
            return gate_services.gate_buy_futures_contract(entry, long_order)
        if exchange_name == 'MEXC':
            return mexc_services.mexc_buy_futures_contract(entry, long_order)
        if exchange_name == 'BYBIT':
            return bybit_services.bybit_buy_futures_contract(entry, long_order)

    def short_buy(self, short_order, entry):
        exchange_name = short_order.exchange_account.exchange.name
        logger.info("---exchange_name short---")
        logger.info(exchange_name)
        if exchange_name == 'GATE':
            return gate_services.gate_buy_futures_contract(entry, short_order)
        if exchange_name == 'MEXC':
            return mexc_services.mexc_buy_futures_contract(entry, short_order)
        if exchange_name == 'BYBIT':
            return bybit_services.bybit_buy_futures_contract(entry, short_order)


    def check_order(self, order_one, order_two, entry, status):
        """Проверяет результаты ордеров"""
        
        status_one = order_one.get('success')
        status_two = order_two.get('success')

        order_one_obj = order_one.get('order')
        order_two_obj = order_two.get('order')
        
        if status_one and status_two:
            self.update_order_status(order_one_obj, status) # меняем статус ордеров
            self.update_order_status(order_two_obj, status)
            
            notification_order(order_one, order_two) # отправляет уведомлние в чат в тг что все супер и идет дальше
        else:
            self.update_status_entry(entry, "FAILED")

            if status_one:
                self.update_order_status(order_one_obj, status) # меняем статус ордеров
                self.update_order_status(order_two_obj, "FAILED")
            
                notification_order(order_one, order_two) # отправляет уведомление в чат в тг что один открылся а второй упал с ошибкой

                self.close_order(order_one_obj, entry) # закрыть первый ордер
            
            elif status_two:
                self.update_order_status(order_one_obj, "FAILED") # меняем статус ордеров
                self.update_order_status(order_two_obj, status)
            
                notification_order(order_one, order_two) # отправляет уведомление в чат в тг что один открылся а второй упал с ошибкой
            
                self.close_order(order_two_obj, entry) # закрыть второй ордер

            else:
                self.update_order_status(order_one_obj, "FAILED") # меняем статус ордеров
                self.update_order_status(order_two_obj, "FAILED")
            
                notification_order(order_one, order_two) # отправлят уведомление в чат в тг что оба ордера не открылись и упали с ошибкой
            
            sys.exit(1) # завершить процесс        
            
    def update_order_status(self, order, new_status):
        """Обновляет статус ордера"""

        order.status = new_status
        order.save()
    
    def close_order(self, order, entry):
        """Закрывает ордера."""

        order.trade_type = "SHORT" if order.trade_type == "LONG" else "LONG"
        order.save()
        close_result = self.short_buy(order, entry)
        if not close_result.get('success'):
            logger.error("Ошибка закрытия ордера.")
