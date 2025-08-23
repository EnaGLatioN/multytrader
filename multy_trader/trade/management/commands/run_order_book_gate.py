from gate.models import OrderBook, WaletPairs
from django.core.management.base import BaseCommand
import logging
import json
import asyncio
import websockets
from collections import OrderedDict
from asgiref.sync import sync_to_async


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OrderBookSocket:
    def __init__(self):
        self.order_book = {'bids': OrderedDict(), 'asks': OrderedDict()}
        self.last_update_id = None

    async def subscribe_to_order_book(self, uri):
        async with websockets.connect(uri) as websocket:
            subscription_message = {
                'time': 1752488982,
                'channel': 'futures.order_book_update',
                'event': 'subscribe',
                'payload': ['BTC_USDT', '100ms', '5']
            }
            await websocket.send(json.dumps(subscription_message))
            response = await websocket.recv()
            logger.info(f"Subscription response: {response}")

            while True:
                message = await websocket.recv()
                await self.process_update(json.loads(message))
                self.print_order_book()

    def print_order_book(self):
        """Выводит стакан в терминал в ASCII-формате"""
        print("\n" + "=" * 60)
        print(f"BTC/USDT Order Book (Spread: {self.get_spread():.2f})")
        print("-" * 60)
        print(f"{'Bids':^30} | {'Asks':^30}")
        print("-" * 60)

        bids = list(self.order_book['bids'].items())[:10]
        asks = list(self.order_book['asks'].items())[:10]

        for i in range(10):
            bid = bids[i] if i < len(bids) else ("", "")
            ask = asks[i] if i < len(asks) else ("", "")

            bid_str = f"{bid[0]:.2f} ({bid[1]:.4f})" if bid[0] else ""
            ask_str = f"{ask[0]:.2f} ({ask[1]:.4f})" if ask[0] else ""

            print(f"{bid_str:>30} | {ask_str:<30}")

    def get_spread(self):
        if not self.order_book['bids'] or not self.order_book['asks']:
            return 0
        return next(iter(self.order_book['asks'])) - next(iter(self.order_book['bids']))

    async def process_update(self, update):
        """Обработка обновления стакана"""
        try:
            result = update.get('result')
            if not result:
                return

            if not all(k in result for k in ['U', 'u', 'b', 'a']):
                return

            if self.last_update_id is None:
                self.last_update_id = result['u']
                return

            if result['u'] <= self.last_update_id:
                return

            if result['U'] <= self.last_update_id + 1 and result['u'] >= self.last_update_id + 1:
                self.apply_update(result['b'], 'bids')
                self.apply_update(result['a'], 'asks')
                self.last_update_id = result['u']
                await self.save_to_db()

        except Exception as e:
            logger.error(f"Error processing update: {e}")

    def apply_update(self, updates, side):
        """Обновление стакана"""
        for update in updates:
            try:
                price = float(update['p'])
                size = float(update['s'])
            except (ValueError, TypeError):
                continue

            if size == 0:
                self.order_book[side].pop(price, None)
            else:
                self.order_book[side][price] = size

        # Сортировка
        self.order_book[side] = OrderedDict(
            sorted(self.order_book[side].items(), reverse=(side == 'bids'))
        )

    async def save_to_db(self):
        if self.order_book['bids'] and self.order_book['asks']:
            top_bid = next(iter(self.order_book['bids']))
            top_ask = next(iter(self.order_book['asks']))
            await sync_to_async(OrderBook.objects.create)(
                symbol='BTC_USDT',
                current_bid=top_bid,
                current_ask=top_ask,
                spread=top_ask - top_bid
            )


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.run_order_book()

    def run_order_book(self):
        uri = "wss://fx-ws.gateio.ws/v4/ws/usdt"
        order_book = OrderBookSocket()
        try:
            asyncio.run(order_book.subscribe_to_order_book(uri))
        except KeyboardInterrupt:
            print("\nOrder book monitoring stopped")
