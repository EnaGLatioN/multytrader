import logging
import requests
from multy_trader.settings import TG_TOKEN

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def notification(entry):
    if chat_id := entry.chat_id:
        send_telegram_message(get_entry_message(entry),chat_id)

def notification_order(order_one, order_two):
    if chat_id := order_one.get('order').entry.chat_id:
        send_telegram_message(get_order_message(order_one, order_two),chat_id)

def get_entry_message(entry):
    """Формирует сообщение для отправки в чат тг"""

    status = entry.status
    status_emoji = {
        'WAIT': '⏳',
        'STOPPED': '⛔️',
        'ACTIVE': '♻️',
        'COMPLETED': '✅',
        'FAILED': '❌',
    }.get(status, '❓')
    
    message = (
        f"{status_emoji} Вход {entry.id}\n"
        f"📊 Статус: {status}\n"
        f"💰 Профит: {entry.profit}\n"
        f"⚖️ Плечо: {entry.shoulder if entry.shoulder else '-'}\n"
        f"🔵 Курс входа: {entry.entry_course}\n"
        f"🔴 Курс выхода: {entry.exit_course if entry.exit_course else '-'}\n"
        f"💹 Валютная пара: {entry.wallet_pair}\n"
        f"🕒 Создан: {entry.created_at.strftime('%Y-%m-%d %H:%M')}"
    )
    return message


def get_order_message(order_one, order_two):
    """Формирует сообщение для отправки в чат тг"""
    
    message = (
        f"Ордер №1\n"
        f"📊 Статус: {order_one.get('order').status}\n"
        f"{order_one.get('result') if order_one.get('success') else order_one.get('error')}\n\n"
        f"Ордер №2\n"
        f"📊 Статус: {order_two.get('order').status}\n"
        f"{order_two.get('result') if order_two.get('success') else order_two.get('error')}\n"
    )
    return message


def send_telegram_message(message, chat_id):
    """Отправляет сообщение в чат тг"""

    try:
        payload = {
            'chat_id': chat_id,
            'text': message
        }
        response = requests.post(f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage', json=payload)
        if response.status_code != 200:
            logger.error(f"Ошибка отправки уведомления в чат {chat_id}: {response.text}")
        else:
            logger.debug(f"Уведомление отправлено в чат {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка в send_telegram_message: {str(e)}")
