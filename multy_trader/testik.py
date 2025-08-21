import ccxt
from django.conf import settings
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'multy_trader.settings')
django.setup()


def buy_btc_ccxt(btc_amount: float):
    """Покупка BTC через CCXT"""
    exchange = ccxt.mexc({
        'apiKey': settings.MEXC_API_KEY,
        'secret': settings.MEXC_API_SECRET,
        'enableRateLimit': True,
    })

    exchange.load_markets()

    # Эти форматы поддерживаются но какой нужен хз"
    symbol_formats = [
        "BTC/USDT:USDT",
        "BTC2/USDT",
        "BTCBAM/USDT",
        "BTCMT/USDT",
        "PBTC/USDT",
        "PUMPBTC/USDT",
        "PUMPBTC/USDT:USDT",
        "WBTC/USDT",
    ]

    for symbol in symbol_formats:
        try:
            print(f"Пробуем символ: {symbol}")
            order = exchange.create_order(
                symbol,
                'market',
                'buy',
                btc_amount
            )
            return order
        except Exception as e:
            print(f"Ошибка с символом {symbol}: {e}")
            continue

    return None






#ПРОВЕРКА ДОСТУПНЫХ ДЛЯ ТОРГОВЛИ ПАР

import ccxt
from django.conf import settings
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'multy_trader.settings')
django.setup()


def check_symbols():
    exchange = ccxt.mexc({
        'apiKey': settings.MEXC_API_KEY,
        'secret': settings.MEXC_API_SECRET,
    })

    exchange.load_markets()

    # Посмотрим все доступные символы
    print("Доступные символы:")
    for symbol in exchange.symbols:
        if 'BTC' in symbol and 'USDT' in symbol:
            print(symbol)

    # Посмотрим информацию о конкретном рынке
    try:
        market = exchange.market('BTC/USDT')
        print("Информация о BTC/USDT:", market)
    except Exception as e:
        print("Ошибка получения market info:", e)


if __name__ == "__main__":
    check_symbols()
    result = buy_btc_ccxt(0.001)  # 0.001 BTC вместо 12
    print("Order result:", result)