import os
import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_telegram_notification(contact_request):
    """
    Отправляет уведомление о новой заявке в Telegram (синхронная версия)
    """
    try:
        bot_token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
        
        # Проверка наличия токена и chat_id
        if not bot_token or not chat_id:
            logger.error("TELEGRAM_BOT_TOKEN или TELEGRAM_CHAT_ID не настроены")
            return False
        
        # Форматирование сообщения
        service_display = dict(contact_request.SERVICE_CHOICES).get(
            contact_request.service, 
            'Не указана'
        )
        
        message = f"""
🔔 <b>НОВАЯ ЗАЯВКА С САЙТА</b>

👤 <b>Имя:</b> {contact_request.name}
📧 <b>Email:</b> {contact_request.email}
🛠 <b>Услуга:</b> {service_display}

💬 <b>Сообщение:</b>
{contact_request.message or 'Не указано'}

📅 <b>Дата:</b> {contact_request.created_at.strftime('%d.%m.%Y %H:%M')}
🆔 <b>ID заявки:</b> #{contact_request.id}
        """.strip()
        
        # URL для API Telegram
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        # Параметры запроса
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        # Отправка запроса
        response = requests.post(url, data=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                # Сохранение ID сообщения
                contact_request.telegram_sent = True
                contact_request.telegram_message_id = result['result']['message_id']
                contact_request.save()
                
                logger.info(f"Уведомление отправлено для заявки #{contact_request.id}")
                return True
            else:
                logger.error(f"Telegram API вернул ошибку: {result}")
                return False
        else:
            logger.error(f"Ошибка HTTP {response.status_code}: {response.text}")
            return False
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка запроса к Telegram API: {e}")
        return False
    except Exception as e:
        logger.error(f"Неожиданная ошибка при отправке в Telegram: {e}")
        return False


# Для совместимости - если где-то используется старое название
send_telegram_notification_sync = send_telegram_notification


def test_telegram_connection():
    """
    Тестирует подключение к Telegram боту
    """
    try:
        bot_token = settings.TELEGRAM_BOT_TOKEN
        
        if not bot_token:
            return False, "TELEGRAM_BOT_TOKEN не настроен"
        
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                bot_info = result['result']
                return True, f"Бот подключен: @{bot_info.get('username')}"
            else:
                return False, f"Ошибка API: {result}"
        else:
            return False, f"HTTP ошибка: {response.status_code}"
            
    except Exception as e:
        return False, f"Ошибка подключения: {e}"