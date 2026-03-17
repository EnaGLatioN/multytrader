import ccxt
import logging
from trade.models import TradeType, Order

logger = logging.getLogger(__name__)


def okx_futures_trade(ready_order):
    proxy = ready_order.proxy
    symbol = ready_order.wallet_pair.local_name
    coin_count = ready_order.wallet_pair.coin_count

    try:
        exchange = ccxt.okx({
            'apiKey': ready_order.api_key,
            'secret': ready_order.secret_key,
            'password': ready_order.passphrase, # У OKX обязателен Passphrase!
            'enableRateLimit': True,
            'proxies': proxy.get_proxies() if proxy else None,
            'options': {
                'defaultType': 'swap', # OKX фьючерсы называются swap
            }
        })

        # Установка плеча на OKX
        try:
            # Для OKX часто нужно указывать 'mgnMode': 'cross' или 'isolated'
            exchange.set_leverage(ready_order.shoulder, symbol, {'mgnMode': 'isolated'})
            logger.info(f"⚖️ OKX: Плечо {ready_order.shoulder}x установлено")
        except Exception as e:
            logger.warning(f"OKX: Плечо не изменено: {e}")

        side = 'buy' if ready_order.trade_type == TradeType.LONG else 'sell'

        # Параметры ордера
        # Важно: на OKX 'amount' может быть в контрактах, а не в монетах. 
        # Если используешь рыночный ордер, проверь, что ready_order.profit — это кол-во контрактов.
        order_ex = exchange.create_market_order(
            symbol=symbol,
            side=side,
            amount=int(ready_order.profit / coin_count) if coin_count else 0,
            params={
                'tdMode': 'isolated', # Trade Mode: изолированная маржа
            }
        )
        
        order_obj = Order.objects.get(id=ready_order.id)
        order_obj.ex_order_id = order_ex['id']
        order_obj.save()

        return {'success': True, 'result': f"✅ OKX: ID {order_ex['id']}"}

    except ccxt.InsufficientFunds as e:
        return {'success': False, 'error': f"❌ OKX: Недостаточно средств: {e}"}
    except Exception as e:
        logger.error(f"❌ OKX Error: {e}")
        return {'success': False, 'error': f"❌ OKX: {str(e)}"}
