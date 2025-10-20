import ccxt
import logging
from trade.models import TradeType
from multy_trader import settings
from utils import get_wallet_pair


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def bybit_buy_futures_contract(entry, order):

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
    exchange_account = order.exchange_account
    proxy = order.proxy

    try:
        # Инициализация для mainnet
        exchange = ccxt.bybit({
            'apiKey': exchange_account.api_key,
            'secret': exchange_account.secret_key,
            'sandbox': False,  # FALSE для mainnet!
            'proxies': proxy.get_proxies() if proxy else None,
            'options': {
                'defaultType': 'linear',
            },
            'enableRateLimit': True,
        })
        logger.debug(f"Конфигурация прокси: {exchange.proxies}")
        # logger.info("🔗 Подключаемся к Bybit mainnet...")

        wallet_pair = get_wallet_pair(entry.wallet_pair, exchange_account.exchange.name)

        try:
            exchange.set_leverage(entry.shoulder, wallet_pair)
            logger.info(f"⚖️ Плечо установлено: {entry.shoulder}x")
        except Exception as e:
            logger.warning(f"Не удалось установить плечо: {e}")

        order_params = {
            'symbol': wallet_pair,
            'type': 'market',
            'side': 'buy' if order.trade_type == TradeType.LONG else 'sell',
            'amount': entry.profit,
            'params': {
                'reduceOnly': False,
            }
        }
        # logger.info(f"🛒 Создаем ордер: {order_params}")

        order_ex = exchange.create_order(**order_params)
        msg = f"✅ Ордер создан успешно! ID: {order_ex['id']}"
        logger.info(msg)
        order.ex_order_id = order_ex['id'] if order_ex['id'] else None
        order.save()
        return {'success': True, 'result': msg, 'order': order}


    except ccxt.AuthenticationError as e:
        error_msg = "❌ Ошибка аутентификации. Проверьте:"
        error_msg += "\n1. Ключи созданы на https://www.bybit.com/"
        error_msg += "\n2. Включены права на Trade"
        error_msg += "\n3. Нет ограничений по IP"
        error_msg += f"\nДетали: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg, 'order': order}

    except ccxt.InsufficientFunds as e:
        error_msg = f"❌ Недостаточно средств: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg, 'order': order}

    except Exception as e:
        error_msg = f"❌ Ошибка: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg, 'order': order}


def get_balance_mainnet(api_key: str, api_secret: str):
    """Получение баланса mainnet"""
    exchange = ccxt.bybit({
        'apiKey': api_key,
        'secret': api_secret,
        'sandbox': False,
    })

    balance = exchange.fetch_balance()
    return balance


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
