import os
import time
import sys
import signal
import django
import logging
from django.core.management.base import BaseCommand
from collections import defaultdict
from trade.models import Entry
from exchange.models import Exchange
from trade.services.price_checker import PriceChecker, PriceCheckerFactory
from trade.services.ready_order import ReadyOrder, ReadyOrderFactory
from trade.services.send_order import opening_orders, closed_orders, update_status_entry


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'multy_trader.settings')
django.setup()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.open_orders = None
        
        signal.signal(signal.SIGTERM, self.handle_exit_signal)

    def add_arguments(self, parser):
        parser.add_argument('--entry_id',  type=str, nargs='?', help='id входа ордера')
        parser.add_argument('--restart', action='store_true', help='Перезапуск')

    def handle(self, *args, **options):
        self.trade(self.get_entry(options.get("entry_id")), options.get("restart"))
    
    def handle_exit_signal(self, signum, frame):
        logger.info("Получен сигнал на остановку процесса...")
        if self.open_orders:
            logger.info("Обнаружены открытые ордера, закрываю перед выходом...")
            closed_orders(self.open_orders, self.entry)
        else:
            logger.info("Открытых ордеров нет...")
        logger.info("Процесс плавно завершен.")
        sys.exit(0)
    
    def forced_closure(self, open_orders, entry):
        closed_orders(open_orders, entry)

    def get_entry(self, entry_id):
        return Entry.objects.prefetch_related("wallet_pair__exchange_mappings").get(id = entry_id)

    def get_orders(self, entry):
        return entry.order_entry.select_related("exchange_account__exchange").all()

    def get_price_checker(self, entry):
        """Тут только нужная информация для проверки цены (по одному ордеру с каждой биржи)"""

        orders_for_price_checker = {}
        ready_order_for_send = defaultdict(list)

        for order in self.get_orders(entry).iterator():
            local_name = entry.wallet_pair.exchange_mappings.get(exchange = order.exchange_account.exchange)
            ready_order_for_send[order.trade_type].append(ReadyOrderFactory.create_ready_order(local_name, order, entry))

            if not orders_for_price_checker.get(order.trade_type):
                orders_for_price_checker[order.trade_type] = PriceCheckerFactory.create_price_checker(local_name, order)
        
        return orders_for_price_checker, ready_order_for_send

    def getter_course(self, orders_for_price_checker):
        bid = orders_for_price_checker.get('LONG').get_bid_ask_prices()
        ask = orders_for_price_checker.get('SHORT').get_bid_ask_prices()
        return (ask.get("best_bid") / (bid.get("best_ask")) - 1) * 100

    def checking_for_open(self, entry, getter_course):
        """Проверка условий входа"""

        if entry.entry_course > 0:
            if entry.reverse: # пока временно оставила
                return getter_course >= entry.entry_course
            return getter_course >= entry.entry_course

        elif entry.entry_course < 0:
            if entry.reverse: # пока временно оставила
                return getter_course <= entry.entry_course
            return getter_course <= entry.entry_course
    
    def checking_for_close(self, entry, getter_course):
        """Проверка условий выхода"""
        
        exit_course = entry.exit_course

        if entry.entry_course > 0:
            if entry.reverse:
                return getter_course >= exit_course
            return getter_course <= exit_course

        elif entry.entry_course < 0:
            if entry.reverse:
                return getter_course <= exit_course
            return getter_course >= exit_course
           
    def reverse_price_checker(self, price_checker):
        reverse_price_checker = {}
        reverse_price_checker['SHORT'] = price_checker.get('LONG')
        reverse_price_checker['LONG'] = price_checker.get('SHORT')
        return reverse_price_checker

    def close_order(self, open_orders, entry, flag = True):
        while flag:
            #entry.refresh_from_db()
            price_checker, _ = self.get_price_checker(entry)
            reverse_price_checker = self.reverse_price_checker(price_checker)
            getter_course = self.getter_course(reverse_price_checker)
            if self.checking_for_close(entry, getter_course):
                flag = False
                return closed_orders(open_orders, entry)
        
    def open_order(self, entry, flag = True):
        while flag:
            #entry.refresh_from_db()
            price_checker, ready_order_for_send = self.get_price_checker(entry)
            getter_course = self.getter_course(price_checker)
            # ГДЕ-ТО НУЖНО ДОБАВИТЬ ПРОВЕРКУ НА ВАЛЮТНУЮ ПАРУ
            logger.info(getter_course)
            logger.info(entry.entry_course)
            logger.info(self.checking_for_open(entry, getter_course))
            logger.info('-------------------------------------------')
            if self.checking_for_open(entry, getter_course): ###
                flag = False
                if open_orders := opening_orders(ready_order_for_send, entry):
                    self.open_orders = open_orders
                    if closed := self.close_order(open_orders, entry):
                        self.open_orders = None
                        return True

    def trade(self, entry, restart):
        logger.info('START')
        logger.info(f'{restart=}')
        while True:
            update_status_entry(entry, "COMPLETED")
            success = self.open_order(entry)
            entry.refresh_from_db()
            logger.info(f'{entry.status}')
            if restart and success and entry.status == 'COMPLETED':
                logger.info("Сделка завершена")
                update_status_entry(entry, "WAIT")
                continue
            
            break
                  