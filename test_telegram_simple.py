import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_telegram():
    print("=" * 60)
    print("ТЕСТ ПОДКЛЮЧЕНИЯ К TELEGRAM")
    print("=" * 60)
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '')
    
    print(f"\n📋 Настройки из .env:")
    print(f"   TELEGRAM_BOT_TOKEN: {'✅ Установлен' if bot_token else '❌ НЕ УСТАНОВЛЕН'}")
    print(f"   TELEGRAM_CHAT_ID: {'✅ Установлен' if chat_id else '❌ НЕ УСТАНОВЛЕН'}")
    
    if not bot_token:
        print("\n❌ ОШИБКА: TELEGRAM_BOT_TOKEN не найден в .env")
        print("\nИнструкция:")
        print("1. Найдите @BotFather в Telegram")
        print("2. Отправьте /newbot")
        print("3. Следуйте инструкциям")
        print("4. Скопируйте токен")
        print("5. Добавьте в .env файл:")
        print("   TELEGRAM_BOT_TOKEN=ваш_токен_здесь")
        return False
    
    if not chat_id:
        print("\n❌ ОШИБКА: TELEGRAM_CHAT_ID не найден в .env")
        print("\nИнструкция:")
        print("1. Найдите @userinfobot в Telegram")
        print("2. Отправьте любое сообщение")
        print("3. Скопируйте ваш Chat ID")
        print("4. Добавьте в .env файл:")
        print("   TELEGRAM_CHAT_ID=ваш_chat_id_здесь")
        return False
    
    print("\n🔄 Тестирование подключения к боту...")
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                bot_info = result['result']
                print(f"✅ Бот подключен успешно!")
                print(f"   Имя: {bot_info.get('first_name')}")
                print(f"   Username: @{bot_info.get('username')}")
                print(f"   ID: {bot_info.get('id')}")
            else:
                print(f"❌ Ошибка API: {result}")
                return False
        else:
            print(f"❌ HTTP ошибка {response.status_code}")
            if response.status_code == 401:
                print("   Токен бота неправильный!")
                print("   Получите новый токен у @BotFather")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка подключения: {e}")
        return False
    
    print("\n🔄 Тестирование отправки сообщения...")
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        test_message = """
🧪 <b>ТЕСТОВОЕ СООБЩЕНИЕ</b>

Это тестовое сообщение для проверки работы бота.

Если вы видите это сообщение - всё работает отлично! ✅

📅 Время: сейчас
        """.strip()
        
        payload = {
            'chat_id': chat_id,
            'text': test_message,
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, data=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Тестовое сообщение отправлено успешно!")
                print("   Проверьте Telegram - должно прийти уведомление")
                return True
            else:
                print(f"❌ Ошибка отправки: {result}")
                return False
        else:
            print(f"❌ HTTP ошибка {response.status_code}")
            if response.status_code == 400:
                print("   Chat ID неправильный!")
                print("   Убедитесь что:")
                print("   1. Вы отправили хотя бы одно сообщение боту")
                print("   2. Chat ID правильный (получите у @userinfobot)")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка отправки: {e}")
        return False


if __name__ == '__main__':
    print("\n")
    success = test_telegram()
    print("\n" + "=" * 60)
    
    if success:
        print("✅ ВСЁ РАБОТАЕТ! Можете запускать сервер.")
        print("\nСледующие шаги:")
        print("1. python manage.py makemigrations")
        print("2. python manage.py migrate")
        print("3. python manage.py runserver")
        print("4. Откройте сайт и протестируйте форму")
    else:
        print("❌ ЕСТЬ ПРОБЛЕМЫ. Исправьте ошибки выше.")
        print("\nПосле исправления запустите снова:")
        print("python test_telegram_simple.py")
    
    print("=" * 60)
    print("\n")