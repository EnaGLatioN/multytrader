from functools import reduce

import ccxt
import logging
from trade.models import (
    TradeType,
    Order
)
from multy_trader import settings
from utils import get_wallet_pair


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def bybit_buy_futures_contract(ready_order, **kwargs):

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

    proxy = ready_order.proxy
    wallet_pair = ready_order.wallet_pair.local_name
    try:
        # Инициализация для mainnet
        exchange = ccxt.bybit({
            'apiKey': ready_order.api_key,
            'secret': ready_order.secret_key,
            'sandbox': False,  # FALSE для mainnet!
            'proxies': proxy.get_proxies() if proxy else None,
            'options': {
                'defaultType': 'linear',
            },
            'enableRateLimit': True,
        })
        logger.debug(f"Конфигурация прокси: {exchange.proxies}")
        # logger.info("🔗 Подключаемся к Bybit mainnet...")
        reduce_only = kwargs.get('reduce_only', False)
        try:
            exchange.set_leverage(ready_order.shoulder, wallet_pair)
            logger.info(f"⚖️ Плечо установлено: {ready_order.shoulder}x")
        except Exception as e:
            logger.warning(f"Не удалось установить плечо: {e}")
        if reduce_only:
            position_idx = 1 if ready_order.trade_type == TradeType.SHORT else 2
        else:
            position_idx = 1 if ready_order.trade_type == TradeType.LONG else 2
        logger.info(ready_order.profit)
        order_params = {
            'symbol': wallet_pair,
            'type': 'market',
            'side': 'buy' if ready_order.trade_type == TradeType.LONG else 'sell',
            'amount': ready_order.profit,
            'params': {
                'reduceOnly': kwargs.get('reduce_only', False),
                'positionIdx': position_idx
            }
        }
        # logger.info(f"🛒 Создаем ордер: {order_params}")

        order_ex = exchange.create_order(**order_params)
        msg = f"✅ Ордер создан успешно! ID: {order_ex['id']}"
        logger.info(msg)
        order = Order.objects.get(id=ready_order.id)
        order.ex_order_id = order_ex['id'] if order_ex['id'] else None
        order.save()
        return {'success': True, 'result': msg, 'order': ready_order}


    except ccxt.AuthenticationError as e:
        error_msg = "❌ Ошибка аутентификации. Проверьте:"
        error_msg += "\n1. Ключи созданы на https://www.bybit.com/"
        error_msg += "\n2. Включены права на Trade"
        error_msg += "\n3. Нет ограничений по IP"
        error_msg += f"\nДетали: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg, 'order': ready_order}

    except ccxt.InsufficientFunds as e:
        error_msg = f"❌ Недостаточно средств: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg, 'order': ready_order}

    except Exception as e:
        error_msg = f"❌ Ошибка: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg, 'order': ready_order}


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

def get_bybit_balance(ready_order):
    proxy = ready_order.proxy
    
    exchange = ccxt.bybit({
        'apiKey': ready_order.api_key,
        'secret': ready_order.secret_key,
        'proxies': proxy.get_proxies() if proxy else None,
        'options': {
            'defaultType': 'linear', # для USDT-фьючерсов
        },
    })

    try:
        balance = exchange.fetch_balance() 
        
        usdt_info = balance.get('USDT', {})
        
        usdt_free = usdt_info.get('free', 0)
        usdt_total = usdt_info.get('total', 0)
        
        logger.info(f"💰 Баланс USDT: Доступно: {usdt_free}, Всего: {usdt_total}")
        return usdt_free, usdt_total

    except Exception as e:
        logger.error(f"❌ Не удалось получить баланс через прокси: {e}")
        return "Не удалось узнать баланс аккаунта"

