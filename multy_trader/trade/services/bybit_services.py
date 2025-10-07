import ccxt
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def buy_future_bybit_mainnet(api_key: str, api_secret: str, symbol: str, amount: float,
                             order_type: str = 'market', price: float = None,
                             leverage: int = 10, reduce_only: bool = False):
    """
    Покупка фьючерса на Bybit mainnet

    :param api_key: API ключ от mainnet
    :param api_secret: Секретный ключ от mainnet
    :param symbol: Торговая пара (BTC/USDT:USDT)
    :param amount: Количество
    :param order_type: 'market' или 'limit'
    :param price: Цена для лимитных ордеров
    :param leverage: Плечо
    :param reduce_only: Только уменьшение позиции
    :return: Результат ордера
    """

    try:
        # Инициализация для mainnet
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'sandbox': False,  # FALSE для mainnet!
            'options': {
                'defaultType': 'linear',
            },
            'enableRateLimit': True,
        })

        logger.info("🔗 Подключаемся к Bybit mainnet...")

        # Загружаем рынки
        markets = exchange.load_markets()
        logger.info(f"✅ Рынки загружены, проверяем символ {symbol}")

        # Проверяем доступность символа
        if symbol not in markets:
            available_symbols = [s for s in markets.keys() if 'USDT' in s][:5]
            raise Exception(f"Символ {symbol} не найден. Доступные: {available_symbols}")

        # Проверяем баланс
        balance = exchange.fetch_balance()
        usdt_balance = balance['total'].get('USDT', 0)
        logger.info(f"💰 Баланс USDT: {usdt_balance}")

        if usdt_balance <= 0:
            raise Exception("Недостаточно USDT на балансе")

        # Устанавливаем плечо
        try:
            exchange.set_leverage(leverage, symbol)
            logger.info(f"⚖️ Плечо установлено: {leverage}x")
        except Exception as e:
            logger.warning(f"Не удалось установить плечо: {e}")

        # Параметры ордера
        order_params = {
            'symbol': symbol,
            'type': order_type,
            'side': 'buy',
            'amount': amount,
            'params': {
                'reduceOnly': reduce_only,
            }
        }

        # Для лимитных ордеров добавляем цену
        if order_type == 'limit' and price is not None:
            order_params['price'] = price

        logger.info(f"🛒 Создаем ордер: {order_params}")

        # Создаем ордер
        order = exchange.create_order(**order_params)

        logger.info(f"✅ Ордер создан успешно! ID: {order['id']}")
        return {
            'success': True,
            'order_id': order['id'],
            'symbol': order['symbol'],
            'side': order['side'],
            'type': order['type'],
            'amount': order['amount'],
            'price': order.get('price'),
            'status': order['status']
        }

    except ccxt.AuthenticationError as e:
        error_msg = "❌ Ошибка аутентификации. Проверьте:"
        error_msg += "\n1. Ключи созданы на https://www.bybit.com/"
        error_msg += "\n2. Включены права на Trade"
        error_msg += "\n3. Нет ограничений по IP"
        error_msg += f"\nДетали: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}

    except ccxt.InsufficientFunds as e:
        error_msg = f"❌ Недостаточно средств: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}

    except Exception as e:
        error_msg = f"❌ Ошибка: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg}


# Дополнительные функции
def get_balance_mainnet(api_key: str, api_secret: str):
    """Получение баланса mainnet"""
    exchange = ccxt.bybit({
        'apiKey': api_key,
        'secret': api_secret,
        'sandbox': False,
    })

    balance = exchange.fetch_balance()
    return balance


def cancel_order_mainnet(api_key: str, api_secret: str, order_id: str, symbol: str):
    """Отмена ордера"""
    exchange = ccxt.bybit({
        'apiKey': api_key,
        'secret': api_secret,
        'sandbox': False,
    })

    return exchange.cancel_order(order_id, symbol)


# Пример использования
if __name__ == "__main__":
    # Ваши реальные ключи от mainnet
    from multy_trader.multy_trader import settings

    API_KEY = settings.BYBIT_API_KEY
    API_SECRET = settings.BYBIT_SECRET_KEY

    # Пример покупки
    result = buy_future_bybit_mainnet(
        api_key=API_KEY,
        api_secret=API_SECRET,
        symbol="BTC/USDT:USDT",
        amount=0.001,
        order_type='market',
        leverage=10
    )

    print("Результат:", result)

    # Проверка баланса
    balance = get_balance_mainnet(API_KEY, API_SECRET)
    print("Баланс:", balance['total'])

    """ LOGS
    INFO:__main__:🔗 Подключаемся к Bybit mainnet...
INFO:__main__:✅ Рынки загружены, проверяем символ BTC/USDT:USDT
INFO:__main__:💰 Баланс USDT: 5.641e-05
INFO:__main__:⚖️ Плечо установлено: 10x
INFO:__main__:🛒 Создаем ордер: {'symbol': 'BTC/USDT:USDT', 'type': 'market', 'side': 'buy', 'amount': 0.001, 'params': {'reduceOnly': False}}
ERROR:__main__:❌ Недостаточно средств: bybit {"retCode":110007,"retMsg":"ab not enough for new order","result":{},"retExtInfo":{},"time":1759834563932}
Результат: {'success': False, 'error': '❌ Недостаточно средств: bybit {"retCode":110007,"retMsg":"ab not enough for new order","result":{},"retExtInfo":{},"time":1759834563932}'}
Баланс: {'USDC': 0.00257, 'ARB': 0.00012, 'ETH': 5.12e-06, 'USDT': 5.641e-05, 'TAIKO': 0.005}
    
    """
