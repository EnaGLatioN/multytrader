import logging
import requests
from datetime import datetime
from multy_trader.settings import TG_TOKEN

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def first_notification(entry):
    if chat_id := entry.trader.chat_id:
        payload = {
            'chat_id': chat_id,
            'text': get_entry_message(entry)
        }
        return send_telegram_message(payload)

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
        f"Вход {entry.alias}\n"
        f"📊 Статус: {status}\n"
        f"💰 Профит: {entry.profit}\n"
        f"⚖️ Плечо: {entry.shoulder if entry.shoulder else '-'}\n"
        f"🔵 Курс входа: {entry.entry_course}\n"
        f"🔴 Курс выхода: {entry.exit_course if entry.exit_course else '-'}\n"
        f"💹 Валютная пара: {entry.wallet_pair}\n"
        f"🕒 Создан: {datetime.now()}"
    )
    return message


def send_reply_message(entry, text):
    """Отправляет событие как ответ (reply) на главное сообщение входа"""

    if not entry.message_id or not entry.trader.chat_id:
        return None

    payload = {
        'chat_id': entry.trader.chat_id,
        'text': f"📝 {text}",
        'reply_to_message_id': entry.message_id
    }
    send_telegram_message(payload)


def send_telegram_message(payload):
    """Отправляет сообщение в чат тг"""
    proxies = {
        'http': "http://user373432:o5jvwd@178.92.196.166:1430",
        'https': "http://user373432:o5jvwd@178.92.196.166:1430"
    }

    try:
        response = requests.post(f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage', json=payload, proxies=proxies)
        data = response.json()
        if data.get('ok'):
            return data.get('result')
    except Exception as e:
        logger.error(f"Ошибка в send_telegram_message: {str(e)}")
