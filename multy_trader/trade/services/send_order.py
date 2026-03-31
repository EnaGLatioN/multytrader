from concurrent.futures import ThreadPoolExecutor
from .gate_services import gate_buy_futures_contract
from .mexc_services import mexc_buy_futures_contract
from .bybit_services import bybit_buy_futures_contract
from .binance import binance_futures_trade
from .okx import okx_futures_trade
from trade.models import Error, Order
from trade.bot import send_reply_message


exchanges = {
    #'MEXC': mexc_buy_futures_contract,
    'GATE': gate_buy_futures_contract,
    "BYBIT": bybit_buy_futures_contract,
    #'KUCOIN': gate_buy_futures_contract,
    'BINANCE': binance_futures_trade,
    #'HTX': gate_buy_futures_contract,
    #'BINGX': gate_buy_futures_contract,
    #'OURBIT': gate_buy_futures_contract,
    'OKX': okx_futures_trade
}


def send_order_to_exchange_api(orders: list, exchanges: dict, reduce_only=False):
    """Покупка"""

    futures = {}
    with ThreadPoolExecutor(max_workers=len(orders) or 1) as executor:
        for order in orders:
            func = exchanges.get(order.exchange_name)
            if func:
                f = executor.submit(func, order, reduce_only=reduce_only)
                futures[f] = order
            else:
                print(f"Функция для биржи {order.exchange_name} не найдена")
    return futures

def save_error(order_id, error):
    order = Order.objects.get(id = order_id)
    Error.objects.create(
        order=order,
        traceback=error
    )

def progress_check(futures: dict):
    """Проверка покупки"""

    if not futures:
        return False

    results = []
    success_order = []
    for f, ready_order in futures.items():
        try:
            result = f.result()
            if result.get('success'):
                success_order.append(ready_order)
                results.append(True)
            else:
                save_error(ready_order.id, result.get('error'))
                results.append(False)
        except Exception as e:
            save_error(ready_order.id, e)
            results.append(False)
    return all(results), success_order


def change_trade_type(success_order):
    for order in success_order:
        if order.exchange_name != 'BYBIT':
            order.trade_type = "SHORT" if order.trade_type == "LONG" else "LONG"
    return success_order


def update_status_entry(entry, status):
    """Обновляет статус входа"""
    entry.status = status
    entry.is_active = True if status in ['ACTIVE', 'WAIT'] else False
    entry.save()


def opening_orders(ready_order_for_send, entry):

    futures = send_order_to_exchange_api(ready_order_for_send.get('LONG', []), exchanges)
    status_long, success_long_order = progress_check(futures)

    if status_long: # лонги успешно открыты
        futures = send_order_to_exchange_api(ready_order_for_send.get('SHORT', []), exchanges)
        status_short, success_short_order = progress_check(futures)

        if status_short: # шорты успешно открыты
            # Отправить сообщение об успешном открытии
            # Поменять статус входа
            update_status_entry(entry, "ACTIVE")
            send_reply_message(entry, 'Шорты были успешно открыты')
            return change_trade_type(success_long_order + success_short_order)

        else: # ошибка открытия шортов
            # Закрыть открывшиеся лонги и шорты
            reverse_order = change_trade_type(success_long_order + success_short_order)
            futures = send_order_to_exchange_api(reverse_order, exchanges, reduce_only=True)
            # поменять статус
            update_status_entry(entry, "FAILED")
            # Отправить уведомление
            send_reply_message(entry, 'Открытые ордера на лонг и шорт успешно были закрыты')
    
    else: # ошибки открытия лонгов
        if success_long_order: # Закрыть открывшиеся лонги если есть + отправить сообщение
            reverse_order = change_trade_type(success_long_order)
            futures = send_order_to_exchange_api(reverse_order, exchanges, reduce_only=True)
            update_status_entry(entry, "FAILED")
            send_reply_message(entry, 'Открытые ордера на лонг успешно были закрыты')

        else: # отправить сообщение
            update_status_entry(entry, "FAILED")
            send_reply_message(entry, 'Ордера на лонг не открылись')
    return change_trade_type(success_long_order) ###


def closed_orders(open_orders, entry):
    futures = send_order_to_exchange_api(open_orders, exchanges, reduce_only=True)
    status, success_closed_order = progress_check(futures)
    if status: # ордера закрыты
        update_status_entry(entry, "COMPLETED")
        send_reply_message(entry, 'Ордера закрыты')
    else:
        update_status_entry(entry, "FAILED")
        send_reply_message(entry, 'Ошибка закрытия ордеров')
    return status
