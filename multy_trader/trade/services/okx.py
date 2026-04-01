import ccxt
import logging
from trade.models import TradeType, Order

logger = logging.getLogger(__name__)


def okx_futures_trade(ready_order, **kwargs):
    proxy = ready_order.proxy
    symbol = ready_order.wallet_pair.local_name
    coin_count = ready_order.wallet_pair.coin_count
    is_long = ready_order.trade_type == TradeType.LONG
    is_reduce_only = kwargs.get('reduce_only', False)

    # Расчёт количества контрактов
    if coin_count and coin_count > 0:
        amount = int(ready_order.profit / coin_count)
    else:
        amount = 0

    if amount <= 0:
        logger.error(f"❌ Некорректное количество {amount} для ордера {ready_order.id}")
        return {'success': False, 'error': f"Некорректное количество {amount}"}

    if amount < 1:
        amount = 1

    try:
        exchange = ccxt.okx({
            'apiKey': ready_order.api_key,
            'secret': ready_order.secret_key,
            'password': ready_order.passphrase,
            'enableRateLimit': True,
            'proxies': proxy.get_proxies() if proxy else None,
            'options': {'defaultType': 'swap'},
        })

        # Установка плеча (изолированная маржа)
        try:
            exchange.set_leverage(
                leverage=int(ready_order.shoulder),
                symbol=symbol,
                params={'mgnMode': 'isolated'}
            )
            logger.info(f"⚖️ Плечо {ready_order.shoulder}x установлено для {symbol}")
        except Exception as e:
            logger.warning(f"Не удалось установить плечо: {e}")

        side = 'buy' if is_long else 'sell'

        params = {
            'tdMode': 'isolated',
        }

        if is_reduce_only:
            params['reduceOnly'] = True
            logger.info(f"📉 Закрывающий ордер для {symbol}")

        order = exchange.create_market_order(
            symbol=symbol,
            side=side,
            amount=amount,
            params=params
        )

        Order.objects.filter(id=ready_order.id).update(ex_order_id=str(order['id']))

        logger.info(f"✅ Ордер {order['id']} создан для {symbol} (side={side}, amount={amount})")
        return {'success': True, 'result': f"Ордер {order['id']} создан"}

    except ccxt.InsufficientFunds:
        logger.error(f"❌ Недостаточно средств для ордера {ready_order.id}")
        return {'success': False, 'error': "Недостаточно средств"}

    except ccxt.BadRequest as e:
        logger.error(f"❌ Ошибка запроса: {e}")
        return {'success': False, 'error': str(e)}

    except Exception as e:
        logger.error(f"❌ Ошибка OKX: {e}")
        return {'success': False, 'error': str(e)}