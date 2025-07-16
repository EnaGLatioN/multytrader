import json
from .models import OrderBook

def process_order_book_update(raw_data):
    data = json.loads(raw_data)

    if data['event'] == 'update':
        bids = data['result']['b']
        asks = data['result']['a']
        current_bid = bids[0]['p'] if bids else None
        current_ask = asks[0]['p'] if asks else None
        spread = float(current_ask) - float(current_bid) if current_bid and current_ask else None

        return {
            'bids': bids,
            'asks': asks,
            'current_bid': current_bid,
            'current_ask': current_ask,
            'spread': spread
        }
    return None


def save_order_book_update(symbol, processed_data):
    OrderBook.objects.create(
        symbol=symbol,
        current_bid=processed_data['current_bid'],
        current_ask=processed_data['current_ask'],
        spread=processed_data['spread']
    )