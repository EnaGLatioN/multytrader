from django.conf import settings
import ccxt


def mexc_buy_futures_contract(entry, order):
    exchange = ccxt.mexc({
        'apiKey': settings.MEXC_API_KEY,
        'secret': settings.MEXC_API_SECRET,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',  # Указываем тип торговли - фьючерсы
        }
    })
    # order_status = exchange.fetch_order('C02__600297473038323712078', 'AIOUSDT')
    # print(order_status)

    # Загружаем рынки для фьючерсов
    exchange.load_markets()

    # Создание рыночного ордера на фьючерсы
    order = exchange.create_order(
        symbol=entry.wallet_pair.slug,
        type='market',
        side="buy" if order.trade_type == "LONG" else "sell",
        amount=entry.profit,  # Количество контрактов
        params={
            'leverage': entry.shoulder,  # Плечо (опционально)
        }
    )
    return order
#{'id': 'C02__600297473038323712078', 'clientOrderId': None, 'timestamp': 1758904306000, 'datetime': '2025-09-26T16:31:46.000Z', 'lastTradeTimestamp': None, 'status': 'closed', 'symbol': 'AIO/USDT', 'type': 'market', 'timeInForce': 'IOC', 'side': 'buy', 'price': 0.17381, 'triggerPrice': None, 'average': 0.16564401, 'amount': 10.0, 'cost': 1.6564401, 'filled': 10.0, 'remaining': 0.0, 'fee': None, 'trades': [], 'info': {'symbol': 'AIOUSDT', 'orderId': 'C02__600297473038323712078', 'orderListId': '-1', 'clientOrderId': None, 'price': '0.17381', 'origQty': '10', 'executedQty': '10', 'cummulativeQuoteQty': '1.6564401', 'status': 'FILLED', 'stpMode': '', 'timeInForce': None, 'type': 'MARKET', 'side': 'BUY', 'stopPrice': None, 'icebergQty': None, 'time': '1758904306000', 'updateTime': '1758904306000', 'isWorking': True, 'origQuoteOrderQty': '0'}, 'fees': [], 'lastUpdateTimestamp': None, 'postOnly': False, 'reduceOnly': None, 'stopPrice': None, 'takeProfitPrice': None, 'stopLossPrice': None}
