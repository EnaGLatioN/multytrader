import ccxt
import logging
from trade.models import TradeType, Order

logger = logging.getLogger(__name__)


def binance_futures_trade(ready_order):

    proxy = ready_order.proxy
    symbol = ready_order.wallet_pair.local_name 
    
    try:
        exchange = ccxt.binance({
            'apiKey': ready_order.api_key,
            'secret': ready_order.secret_key,
            'enableRateLimit': True,
            'proxies': proxy.get_proxies() if proxy else None,
            'options': {
                'defaultType': 'future',
            }
        })

        try:
            exchange.set_leverage(ready_order.shoulder, symbol)
            logger.info(f"⚖️ Плечо {ready_order.shoulder}x установлено")
        except Exception as e:
            logger.warning(f"Плечо не изменено (возможно, уже такое же): {e}")

        side = 'buy' if ready_order.trade_type == TradeType.LONG else 'sell'

        order_params = {
            'symbol': symbol,
            'type': 'market',
            'side': side,
            'amount': ready_order.profit,
            'params': {
            }
        }

        logger.info(f"🚀 Binance Order: {side} {ready_order.profit} {symbol}")
        
        order_ex = exchange.create_order(**order_params)
        
        order_obj = Order.objects.get(id=ready_order.id)
        order_obj.ex_order_id = order_ex['id']
        order_obj.save()

        return {'success': True, 'result': f"✅ Binance: ID {order_ex['id']}"}

    except ccxt.InsufficientFunds as e:
        return {'success': False, 'error': f"❌ Binance: Недостаточно средств: {e}"}
    except Exception as e:
        logger.error(f"❌ Binance Error: {e}")
        return {'success': False, 'error': f"❌ Binance: {str(e)}"}
