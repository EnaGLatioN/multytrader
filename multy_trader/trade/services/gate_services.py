import ccxt
import logging

from trade.models import TradeType
from gate_api import ApiClient, Configuration, FuturesApi
from gate_api.models import FuturesOrder
from multy_trader.settings import GATE_HOST


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_proxies(proxy):
    # вынесите меня куда-нибудь в общий мусор
    proxy_url = proxy.get_proxy_url()
    return {
        'http': proxy_url,
        'https': proxy_url
    }


def gate_buy_futures_contract(entry, order):
    """
    Функция для покупки фьючерсного контракта на GATE по маркету с установкой плеча

    :param entry: объект entry с данными о торговой паре
    :param order: объект order с данными об ордере
    :param leverage: плечо (по умолчанию 10x)
    """
    symbol = entry.wallet_pair.slug  # Например, BTC_USDT для бессрочного контракта
    amount = entry.profit if order.trade_type == TradeType.LONG else -entry.profit  # Количество BTC превращать из суммы в кол-во

    proxies = None
    if proxy := order.proxy:
        proxies = get_proxies(proxy)

    try:
        exchange = ccxt.gate({
            'apiKey': order.exchange_account.api_key,
            'secret': order.exchange_account.secret_key,
            'enableRateLimit': True,
            'proxies': proxies
        })

        exchange.options['defaultType'] = 'swap'
        exchange.options['defaultSettle'] = 'usdt'
        logger.info(f"Конфигурация прокси: {exchange.proxies}")

        try:
            leverage_response = exchange.set_leverage(
                leverage=entry.shoulder,
                symbol=symbol
            )
            logger.info(f"Плечо установлено: {entry.shoulder}x - {leverage_response}")
        except ccxt.BaseError as leverage_error:
            logger.warning(f"Не удалось установить плечо {entry.shoulder}x: {leverage_error}")

        side = 'buy' if order.trade_type == TradeType.LONG else 'sell'
        order_response = exchange.create_order(
            symbol=symbol,
            type='market',
            side=side,
            amount=abs(amount),
            params={'timeInForce': 'IOC'}
        )
        logger.info(f"Ордер размещён с плечом {entry.shoulder}x: {order_response}")
        return order_response

    except ccxt.BaseError as e:
        logger.error(f"Ошибка при размещении ордера с плечом {entry.shoulder}x: {e}")
        return None

    #try:
    #    config = Configuration(
    #        host=GATE_HOST,
    #        key=order.exchange_account.api_key,
    #        secret=order.exchange_account.secret_key,
    #        proxies=proxies
    #    )
    #    futures_api = FuturesApi(ApiClient(config))
    #    print(futures_api)
    #    settle = 'usdt'
    #    # 1. Сначала устанавливаем плечо
    #    try:
    #        leverage_response = futures_api.update_position_leverage(settle, contract, entry.shoulder)
    #        logger.info(f"Плечо установлено: {entry.shoulder}x - {leverage_response}")
    #    except Exception as leverage_error:
    #        logger.warning(f"Не удалось установить плечо {entry.shoulder}x: {leverage_error}")
    #        # Продолжаем выполнение, так как возможно плечо уже установлено
    #    # 2. Размещаем ордер
    #    futures_order = FuturesOrder(
    #        contract=contract,
    #        size=amount if order.trade_type == TradeType.LONG else -amount,
    #        price="0",  # Для маркет-ордера
    #        tif="ioc"  # Immediate or Cancel - обязательно для маркет-ордера
    #    )
    #
    #    response = futures_api.create_futures_order(settle, futures_order)
    #    logger.info(f"Ордер размещен с плечом {entry.shoulder}x: {response}")
    #    return response
    #
    #except Exception as e:
    #    logger.error(f"Ошибка при размещении ордера с плечом {entry.shoulder}x - gate_buy_futures_contract: {e}")
    #    return None
