from django.conf import settings
import django
import ccxt

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'multy_trader.settings')
django.setup()


def mexc_buy_futures_contract(entry, order):
    exchange = ccxt.mexc({
        'apiKey': settings.MEXC_API_KEY,
        'secret': settings.MEXC_API_SECRET,
        'enableRateLimit': True,
    })

    exchange.load_markets()

    # Создание рыночного ордера на покупку по количеству
    order = exchange.create_order(
        entry.wallet_pair.slug,
        'market',
        "buy" if order.trade_type == "LONG" else "sell",
        entry.count
    )
    return order