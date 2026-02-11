import os
import requests
from django.conf import settings


def send_telegram_notification(contact_request):
    try:
        bot_token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID
        
        if not bot_token or not chat_id:
            return False
        
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
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, data=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                # Сохранение ID сообщения
                contact_request.telegram_sent = True
                contact_request.telegram_message_id = result['result']['message_id']
                contact_request.save()
                
                return True
            else:
                return False
        else:
            return False
        
    except requests.exceptions.RequestException as e:
        return False
    except Exception as e:
        return False


send_telegram_notification_sync = send_telegram_notification


def test_telegram_connection():
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