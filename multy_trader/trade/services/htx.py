import ccxt
import logging
from trade.models import TradeType, Order

logger = logging.getLogger(__name__)


def htx_futures_trade(ready_order, **kwargs):
    proxy = ready_order.proxy
    symbol = ready_order.wallet_pair.local_name
    coin_count = ready_order.wallet_pair.coin_count

    try:
        exchange = ccxt.htx({
            'apiKey': ready_order.api_key,
            'secret': ready_order.secret_key,
            'enableRateLimit': True,
            'proxies': proxy.get_proxies() if proxy else None,
            'options': {
                'defaultType': 'linear', 
            }
        })

        try:
            exchange.set_leverage(int(ready_order.shoulder), symbol)
            logger.info(f"⚖️ HTX: Плечо {ready_order.shoulder}x установлено")
        except Exception as e:
            logger.warning(f"HTX: Плечо не изменено: {e}")

        params = {
            'marginMode': 'isolated',
        }

        if kwargs.get('reduce_only'):
            params['reduceOnly'] = True
            # Для HTX в режиме хеджирования при закрытии часто нужен offset
            #params['offset'] = 'close'

        order_ex = exchange.create_market_order(
            symbol=symbol,
            side='buy' if ready_order.trade_type == TradeType.LONG else 'sell',
            amount=int(ready_order.profit / coin_count) if coin_count else 0,
            params=params
        )
        
        order_obj = Order.objects.get(id=ready_order.id)
        order_obj.ex_order_id = str(order_ex['id'])
        order_obj.save()

        return {'success': True, 'result': f"✅ HTX: ID {order_ex['id']}"}

    except ccxt.InsufficientFunds as e:
        return {'success': False, 'error': f"❌ HTX: Недостаточно средств: {e}"}
    except Exception as e:
        logger.error(f"❌ HTX Error: {e}")
        return {'success': False, 'error': f"❌ HTX: {str(e)}"}
