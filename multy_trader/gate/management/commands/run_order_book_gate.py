import logging
import json
import asyncio
import websockets
from collections import OrderedDict
from asgiref.sync import sync_to_async
from gate.models import OrderBook, WaletPairs
from django.core.management.base import BaseCommand


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OrderBookSocket:
    def __init__(self):
        self.order_book = {'bids': {}, 'asks': {}}
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
            logger.info("Subscription response:", response)

            while True:
                message = await websocket.recv()
                await self.process_update(json.loads(message))

    async def process_update(self, update):
        """Обработка обновления стакана"""
        logger.info("Raw update received:", update)

        try:
            # Извлекаем данные из результата
            result = update.get('result')
            if result is None:
                logger.error("Invalid update format, result missing:", update)
                return

            # Проверяем необходимые поля
            if not all(k in result for k in ['U', 'u', 'b', 'a']):
                logger.error("Invalid update structure:", result)
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

                if self.order_book['bids'] and self.order_book['asks']:
                    top_bid = next(iter(self.order_book['bids']))
                    top_ask = next(iter(self.order_book['asks']))
                    print(f"Update ID: {result['u']} | Bid: {top_bid} | Ask: {top_ask} | Spread: {top_ask - top_bid:.2f}")
                    spread = top_ask - top_bid
                    await self.save_order_book_to_db(top_bid, top_ask, spread)
            else:
                logger.error(f"Out of sync! Local ID: {self.last_update_id}, Update IDs: {result['U']}-{result['u']}")

        except Exception as e:
            logger.error(f"Update processing failed: {str(e)}")


    def apply_update(self, updates, side):
        """Обновление локального стакана"""
        for update in updates:
            try:
                price = float(update['p'])
                size = float(update['s'])
            except (ValueError, TypeError) as e:
                logger.error(f"Could not convert price or size to float. Update: {update}. Error: {e}")
                continue

            if size == 0:
                if price in self.order_book[side]:
                    del self.order_book[side][price]
            else:
                self.order_book[side][price] = size
        if side == 'bids':
            self.order_book[side] = OrderedDict(sorted(self.order_book[side].items(), reverse=True))
        else:
            self.order_book[side] = OrderedDict(sorted(self.order_book[side].items()))

    async def save_order_book_to_db(self, top_bid, top_ask, spread):
        await sync_to_async(OrderBook.objects.create)(
            symbol='BTC_USDT',
            current_bid=top_bid,
            current_ask=top_ask,
            spread=spread
        )


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.order_book()

    def order_book(self):
        uri = "wss://fx-ws.gateio.ws/v4/ws/usdt"
        order_book = OrderBookSocket()
        asyncio.run(order_book.subscribe_to_order_book(uri))


