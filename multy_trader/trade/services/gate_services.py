from gate_api import ApiClient, Configuration, FuturesApi
from trade.models import TradeType
import time
from multy_trader.settings import GATE_HOST


def gate_buy_futures_contract(entry,order):
    """
    Функция для покупки/продажи фьючерсного контракта на GATE
    """

    contract=entry.wallet_pair.slug # Например, BTC_USDT для бессрочного контракта
    amount=entry.profit if order.trade_type == TradeType.LONG else -entry.profit # Количество BTC превращать из суммы в кол-во
    price=entry.entry_course  # None для рыночного ордера
    take_profit=entry.exit_course # Курс выхода
    order_type="market"  # "market" или "limit"

    try:
        config = Configuration(
            host=GATE_HOST,
            key=order.exchange_account.api_key,
            secret=order.exchange_account.secret_key
        )
        futures_api = FuturesApi(ApiClient(config))
        settle = 'usdt'
        futures_api.update_position_leverage(
            contract=contract,
            leverage=str(entry.shoulder),
            settle=settle  # Для USDT-маркированных контрактов
        )

        order = FuturesApi.FuturesOrder(
            contract=contract,
            size=amount,  # Положительное значение для лонга
            price=str(price) if price else None,
            time_in_force="gtc",  # Good Till Cancelled
            close=False,
            reduce_only=False,
            settle=settle.upper(),
            text=f"api-buy-{int(time.time())}"
        )
        if take_profit:
            close_order = FuturesApi.FuturesOrder(
                contract=contract,
                size=amount,  # Такой же объем
                price=str(take_profit),
                time_in_force="gtc",
                close=True,  # Закрытие позиции
                reduce_only=True,  # Только уменьшение позиции
                settle=settle.upper(),
                text=f"tp-{int(time.time())}"
            )
            futures_api.create_futures_order(settle.upper(), close_order)
        response = futures_api.create_futures_order(settle.upper(), order)
        print("Ордер размещен:", response)
        return response

    except Exception as e:
        print("Ошибка при размещении ордера:", e)
        return None
