import logging
from multy_trader.multy_trader import settings

API_KEY = settings.BYBIT_API_KEY
API_SECRET = settings.BYBIT_SECRET_KEY
from trade.models import TradeType
from gate_api import ApiClient, Configuration, FuturesApi
from gate_api.models import FuturesOrder
from multy_trader.settings import GATE_HOST


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def gate_buy_futures_contract(entry,order):
    """
    Функция для покупки фьючерсного контракта на GATE по маркету
    """

    contract=entry.wallet_pair.slug # Например, BTC_USDT для бессрочного контракта
    amount=entry.profit if order.trade_type == TradeType.LONG else -entry.profit # Количество BTC превращать из суммы в кол-во

    try:
        config = Configuration(
            host=GATE_HOST,
            key=order.exchange_account.api_key,
            secret=order.exchange_account.secret_key
        )
        futures_api = FuturesApi(ApiClient(config))
        settle = 'usdt'

        order = FuturesOrder(
            contract=contract,
            size=amount,
            price="0",  # Для маркет-ордера
            tif="ioc"   # Immediate or Cancel - обязательно для маркет-ордера
        )

        response = futures_api.create_futures_order(settle, order)
        logger.info("Ордер размещен:", response)
        return response

    except Exception as e:
        logger.error("Ошибка при размещении ордера: - gate_buy_futures_contract", e)
        return None
