import logging
import requests


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TG_TOKEN='8404279029:AAGuIKjNh90u0deU6tOYH4c9H7scoB1bXGA'

def notification(entry):
    message = get_message(entry)
    chat_id = entry.chat_id
    send_telegram_message(message,chat_id)

def get_message(entry):
    message = 'хуй'
    return message

def send_telegram_message(message, chat_id):
    try:
        payload = {
            'chat_id': chat_id,
            'text': message
        }
        response = requests.post(f'https://api.telegram.org/bot{TG_TOKEN}/sendMessage', json=payload)
        if response.status_code != 200:
            logger.error(f"Ошибка отправки уведомления в чат {chat_id}: {response.text}")
        else:
            logger.info(f"Уведомление отправлено в чат {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка в send_telegram_message: {str(e)}")

if __name__ == '__main__':
    notification()
