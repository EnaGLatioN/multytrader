import ccxt
import logging

from trade.models import TradeType
from multy_trader.settings import GATE_HOST
from utils import get_wallet_pair
from trade.models import Order


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def gate_buy_futures_contract(ready_order, **kwargs):
    """
    Функция для покупки фьючерсного контракта на GATE по маркету
    """
    # amount = entry.profit if order.trade_type == TradeType.LONG else -entry.profit
    symbol = ready_order.wallet_pair.local_name
    coin_count = ready_order.wallet_pair.coin_count
    proxy = ready_order.proxy
    try:
        exchange = ccxt.gate({
            'apiKey': ready_order.api_key,
            'secret': ready_order.secret_key,
            'enableRateLimit': True,
            'proxies': proxy.get_proxies() if proxy else None
        })

        exchange.options['defaultType'] = 'swap'
        exchange.options['defaultSettle'] = 'usdt'

        status_close, msg = close_position(exchange, symbol, coin_count, ready_order)

        if not status_close:
            try:
                exchange.set_leverage(
                    leverage=ready_order.shoulder,
                    symbol=symbol
                )
                logger.info(f"Плечо установлено: {ready_order.shoulder}x")
            except ccxt.BaseError as leverage_error:
                logger.warning(f"Не удалось установить плечо {ready_order.shoulder}x: {leverage_error}")

            print("Q"*50)
            print(int(ready_order.profit / coin_count) if coin_count else 0)
            order_params = {
                'symbol': symbol,
                'type': 'market',
                'side': 'buy' if ready_order.trade_type == TradeType.LONG else 'sell',
                'amount': int(ready_order.profit / coin_count) if coin_count else 0,
                'params': {
                    'timeInForce': 'IOC',
                }
            }

            order_response = exchange.create_order(**order_params)
            msg = f"✅ Новая позиция открыта с плечом {ready_order.shoulder}x: {order_response}"
            logger.info(msg)
            order = Order.objects.get(id=ready_order.id)
            order.ex_order_id = order_response.get('id', None)
            order.save()

        return {'success': True, 'result': msg, 'order': ready_order}

    except ccxt.AuthenticationError as e:
        error_msg = "❌ Ошибка аутентификации. Проверьте:"
        error_msg += "\n1. Ключи созданы на https://www.gate.com"
        error_msg += "\n2. Включены права на Trade"
        error_msg += "\n3. Нет ограничений по IP"
        error_msg += f"\nДетали: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg, 'order': ready_order}

    except ccxt.InsufficientFunds as e:
        error_msg = f"❌ Недостаточно средств: {e}"
        logger.error(error_msg)
        return {'success': False, 'error': error_msg, 'order': ready_order}

    except ccxt.BaseError as e:
        error_msg = f"❌ Ошибка при размещении ордера: {str(e)}"
        logger.error(f"CCXT error: {repr(e)}", exc_info=True)  # Логируем полную информацию
        return {'success': False, 'error': error_msg, 'order': ready_order}

    except Exception as e:
        error_msg = "❌ Ошибка при размещении ордера."
        error_msg += f"\nДетали: {e}"
        logger.error(f"2 CCXT error: {repr(e)}", exc_info=True)  # Логируем полную информацию
        return {'success': False, 'error': error_msg, 'order': ready_order}


def close_position(exchange, symbol, coin_count, ready_order):
    try:
        logger.info(f"🔍 Закрываем позицию для символа {symbol}")
        # 🔥 ПОЛУЧАЕМ ТЕКУЩУЮ ПОЗИЦИЮ
        positions = exchange.fetch_positions([symbol])

        current_position = None
        for position in positions:
            # logger.info(f"ТЕКУЩИЕ ПОЗИЦИИ {position}")
            if position.get("info").get('contract') == symbol and position['contracts'] > 0:
                current_position = position
                break

        if not current_position:
            msg = f"🔍 Активная позиция не найдена для {symbol}"
            logger.info(msg)
            return False, msg # Позиции нет, считаем что закрыта

        logger.info(f"🔍 Найдена позиция: {current_position}")

        # 🔥 ОПРЕДЕЛЯЕМ СТОРОНУ ДЛЯ ЗАКРЫТИЯ
        # Если позиция LONG - закрываем SELL, и наоборот
        side = 'sell' if current_position['side'] == 'long' else 'buy'
        amount = abs(current_position['contracts'])

        logger.info(f"🔄 Закрываем позицию: {side} {amount} контрактов")

        # 🔥 РАЗМЕЩАЕМ ПРОТИВОПОЛОЖНЫЙ ОРДЕР
        close_order_params = {
            'symbol': symbol,
            'type': 'market',
            'side': side,
            'amount': int(ready_order.profit / coin_count) if coin_count else 0,
            'params': {
                'reduceOnly': True,
                'timeInForce': 'IOC',
            }
        }

        close_response = exchange.create_order(**close_order_params)
        msg = f"✅ Позиция закрыта: {close_response}"
        logger.info(msg)
        return True, msg

    except ccxt.BaseError as e:
        msg = f"Ошибка при закрытии позиции: {e}"
        msg += f"\nДетали: {e}"
        logger.error(f"close_position gate error: {repr(e)}", exc_info=True)
        return False, msg
        