from .gate_services import gate_buy_futures_contract
from .mexc_services import mexc_buy_futures_contract
from trade.models import TradeType


exchanges = {
    'MEXC': mexc_buy_futures_contract,
    'GATE': gate_buy_futures_contract
}

def send_order_to_exchange_api(entry):
    """
    Общая функция распределения order по биржам
    """

    orders = entry.order_entry.all()
    for order in orders:
        exchange = exchanges.get(order.exchange_account.exchange.name)
        if exchange:
            exchange(entry, order)
