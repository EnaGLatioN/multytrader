import json
import asyncio
import websockets
from collections import OrderedDict

class OrderBook:
    def __init__(self):
        self.order_book = {'bids': {}, 'asks': {}}
        self.last_update_id = None

    async def subscribe_to_order_book(self, uri):
        async with websockets.connect(uri) as websocket:
            # Подписка на обновления стакана
            subscription_message = {
                'time': 1752488982,  # Это можно изменить на текущее время
                'channel': 'futures.order_book_update',
                'event': 'subscribe',
                'payload': ['BTC_USDT', '100ms', '5']
            }
            await websocket.send(json.dumps(subscription_message))
            response = await websocket.recv()
            print("Subscription response:", response)

            while True:
                message = await websocket.recv()
                await self.process_update(json.loads(message))

    async def process_update(self, update):
        """Обработка обновления стакана"""
        print("Raw update received:", update)

        try:
            # Извлекаем данные из результата
            result = update.get('result')
            if result is None:
                print("Invalid update format, result missing:", update)
                return

            # Проверяем необходимые поля
            if not all(k in result for k in ['U', 'u', 'b', 'a']):
                print("Invalid update structure:", result)
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
            else:
                print(f"Out of sync! Local ID: {self.last_update_id}, Update IDs: {result['U']}-{result['u']}")

        except Exception as e:
            print(f"Update processing failed: {str(e)}")

    def apply_update(self, updates, side):
        """Обновление локального стакана"""
        for update in updates:
            try:
                price = float(update['p'])  # Извлечение цены
                size = float(update['s'])  # Извлечение объема
            except (ValueError, TypeError) as e:
                print(f"Could not convert price or size to float. Update: {update}. Error: {e}")
                continue  # Пропускаем некорректные данные

            if size == 0:
                if price in self.order_book[side]:
                    del self.order_book[side][price]
            else:
                self.order_book[side][price] = size

        # Сортировка стакана
        if side == 'bids':
            self.order_book[side] = OrderedDict(sorted(self.order_book[side].items(), reverse=True))
        else:
            self.order_book[side] = OrderedDict(sorted(self.order_book[side].items()))

if __name__ == "__main__":
    uri = "wss://fx-ws.gateio.ws/v4/ws/usdt"
    order_book = OrderBook()
    asyncio.run(order_book.subscribe_to_order_book(uri))