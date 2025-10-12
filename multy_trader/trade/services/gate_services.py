import ccxt
import logging

from trade.models import TradeType
from multy_trader.settings import GATE_HOST
from utils import get_wallet_pair


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def gate_buy_futures_contract(entry, order):
    """
    Функция для покупки фьючерсного контракта на GATE по маркету
    """

    amount = entry.profit if order.trade_type == TradeType.LONG else -entry.profit
    exchange_account = order.exchange_account
    symbol = get_wallet_pair(entry.wallet_pair, exchange_account.exchange.name)

    proxy = order.proxy

    try:
        exchange = ccxt.gate({
            'apiKey': exchange_account.api_key,
            'secret': exchange_account.secret_key,
            'enableRateLimit': True,
            'proxies': proxy.get_proxies() if proxy else None
        })

        exchange.options['defaultType'] = 'swap'
        exchange.options['defaultSettle'] = 'usdt'

        # Определяем, это закрытие позиции?

        if amount < 0:
            close_position(order, exchange, symbol)

        else:
            # ОТКРЫТИЕ НОВОЙ ПОЗИЦИИ
            try:
                exchange.set_leverage(
                    leverage=entry.shoulder,
                    symbol=symbol
                )
                logger.info(f"Плечо установлено: {entry.shoulder}x")
            except ccxt.BaseError as leverage_error:
                logger.warning(f"Не удалось установить плечо {entry.shoulder}x: {leverage_error}")

            order_params = {
                'symbol': symbol,
                'type': 'market',
                'side': 'buy' if order.trade_type == TradeType.LONG else 'sell',
                'amount': abs(amount),
                'params': {
                    'timeInForce': 'IOC',
                }
            }

            order_response = exchange.create_order(**order_params)
            logger.info(f"✅ Новая позиция открыта с плечом {entry.shoulder}x: {order_response}")
            order.ex_order_id = order_response.get('id', None)
            order.save()
            return order_response

    except ccxt.BaseError as e:
        logger.error(f"Ошибка при размещении ордера: {e}")
        return None


def close_position(order, exchange, symbol):
    try:
        # Получаем ID ордера из объекта order (предполагается что он там есть)
        order_id = order.ex_order_id  # или order.id в зависимости от модели
        close_response = exchange.cancel_order(order_id, symbol)
        logger.info(f"✅ Ордер закрыт по ID {order_id}: {close_response}")
        return close_response
    except ccxt.OrderNotFound as e:
        logger.error(f"Ордер с ID {order_id} не найден: {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при закрытии ордера {order_id}: {e}")
        return None
