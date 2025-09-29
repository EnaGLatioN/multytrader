from gate_api import ApiClient, Configuration, FuturesApi
from gate_api.models import FuturesOrder
import time
from multy_trader.settings import GATE_HOST


def gate_buy_futures_contract():
    """
    Функция для покупки фьючерсного контракта на GATE по маркету
    """

    contract = "AIO_USDT"
    amount = 1

    try:
        config = Configuration(
            host=GATE_HOST,
            key='2a3552173f3b1e48754b465a3e4f8676',
            secret='ca1a878b75c7582fddf9eacace174b36901fcd63713f9392033d6cc2e58e8b1e'
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
        print("Ордер размещен:", response)
        return response

    except Exception as e:
        print("Ошибка при размещении ордера:", e)
        return None

print(gate_buy_futures_contract())