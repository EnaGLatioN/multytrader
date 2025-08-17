import decouple
from gate_api import ApiClient, Configuration, FuturesApi
import time


# Конфигурация API
API_KEY = decouple.config("GATE_KEY")
SECRET_KEY = decouple.config("GATE_SECRET_KEY")

config = Configuration(
    host="https://api.gateio.ws/api/v4",
    key=API_KEY,
    secret=SECRET_KEY
)

# Создаем клиент API
futures_api = FuturesApi(ApiClient(config))


def buy_futures_contract(
        contract="BTC_USDT",  # Например, BTC_USDT для бессрочного контракта
        amount=0.001,  # Количество BTC
        price=None,  # None для рыночного ордера
        leverage=10,  # Плечо
        order_type="market"  # "market" или "limit"
):
    try:
        futures_api.update_position_leverage(
            contract=contract,
            leverage=str(leverage),
            settle='usdt'  # Для USDT-маркированных контрактов
        )

        order = FuturesApi.FuturesOrder(
            contract=contract,
            size=amount,  # Положительное значение для лонга
            price=str(price) if price else None,
            time_in_force="gtc",  # Good Till Cancelled
            close=False,
            reduce_only=False,
            settle="USDT",
            text=f"api-buy-{int(time.time())}"
        )
        response = futures_api.create_futures_order(order)
        print("Ордер размещен:", response)
        return response

    except Exception as e:
        print("Ошибка при размещении ордера:", e)
        return None


# x = buy_futures_contract(
#     contract="BTC_USDT",
#     amount=0.001,
#     price=None,  # Рыночный ордер
#     leverage=1,
#     order_type="market"
# )
# print("=" * 100)
# print(x)
