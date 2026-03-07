## 🧰 Установка

1. Клонируйте репозиторий:

```bash
git clone ...
cd ...
```
2. Создайте виртуальное окружение:

```bash
python -m venv venv
```

3. Установите зависимости:

```bash
pip install -r requirements.txt
```

4.Создать .env

```bash
SECRET_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
LIQPAY_PUBLIC_KEY=...
LIQPAY_PRIVATE_KEY=...
```

5. Выполните миграции БД:
   
```bash
python manage.py migrate
```

6. Создайте суперпользователя (админ-панель):
   
```bash
python manage.py createsuperuser
```

7. Запустите сервер разработки:
```bash
python manage.py runserver
```

