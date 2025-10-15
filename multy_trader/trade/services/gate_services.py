import ccxt
import logging
from trade.bot import send_telegram_message

from trade.models import TradeType
from multy_trader.settings import GATE_HOST
from utils import get_wallet_pair


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def gate_buy_futures_contract(entry, order):
    """
    Функция для покупки фьючерсного контракта на GATE по маркету
    """

    # amount = entry.profit if order.trade_type == TradeType.LONG else -entry.profit
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

        if not close_position(exchange, symbol, entry):
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
                'amount': entry.profit,
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
        send_telegram_message(f"Ошибка при размещении ордера: {e}", entry.chat_id)


def close_position(exchange, symbol, entry):
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
            logger.info(f"🔍 Активная позиция не найдена для {symbol}")
            return False  # Позиции нет, считаем что закрыта

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
            'amount': amount,
            'params': {
                'reduceOnly': True,  # ⚠️ ВАЖНО: только уменьшение позиции
                'timeInForce': 'IOC',
            }
        }

        close_response = exchange.create_order(**close_order_params)
        logger.info(f"✅ Позиция закрыта: {close_response}")
        return True

    except ccxt.BaseError as e:
        logger.error(f"Ошибка при закрытии позиции: {e}")
        send_telegram_message(f"Ошибка при размещении ордера: {e}", entry.chat_id)
