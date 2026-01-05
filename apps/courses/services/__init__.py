"""
Сервис для работы с LiqPay API
Безопасная интеграция с использованием лучших практик
"""

import base64
import hashlib
import json
from typing import Dict, Optional
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class LiqPayService:
    """Сервис для работы с LiqPay"""

    API_URL = "https://www.liqpay.ua/api/3/checkout"

    def __init__(self):
        self.public_key = settings.LIQPAY_PUBLIC_KEY
        self.private_key = settings.LIQPAY_PRIVATE_KEY

        if not self.public_key or not self.private_key:
            raise ValueError("LiqPay ключи не настроены в settings")

    def _generate_signature(self, data: str) -> str:
        """Генерация подписи для запроса"""
        sign_string = self.private_key + data + self.private_key
        signature = base64.b64encode(
            hashlib.sha1(sign_string.encode('utf-8')).digest()
        )
        return signature.decode('utf-8')

    def create_payment_form_data(
            self,
            order_id: str,
            amount: float,
            description: str,
            result_url: str,
            server_url: str,
            currency: str = 'UAH',
            **kwargs
    ) -> Dict[str, str]:
        """
        Создание данных для формы оплаты

        Args:
            order_id: Уникальный ID заказа
            amount: Сумма платежа
            description: Описание платежа
            result_url: URL для редиректа после оплаты
            server_url: URL для callback (server-to-server)
            currency: Валюта (UAH, USD, EUR)
            **kwargs: Дополнительные параметры LiqPay

        Returns:
            Dict с data и signature для формы
        """

        params = {
            'version': '3',
            'public_key': self.public_key,
            'action': 'pay',
            'amount': str(amount),
            'currency': currency,
            'description': description,
            'order_id': order_id,
            'result_url': result_url,
            'server_url': server_url,
            'language': kwargs.get('language', 'uk'),
        }

        # Добавляем опциональные параметры
        optional_params = ['customer', 'customer_user_id', 'product_category',
                           'product_description', 'product_name', 'product_url']

        for param in optional_params:
            if param in kwargs:
                params[param] = kwargs[param]

        # Кодируем данные
        data = base64.b64encode(
            json.dumps(params).encode('utf-8')
        ).decode('utf-8')

        # Генерируем подпись
        signature = self._generate_signature(data)

        logger.info(f"Создана форма оплаты для заказа {order_id}")

        return {
            'data': data,
            'signature': signature,
        }

    def verify_callback(self, data: str, signature: str) -> Optional[Dict]:
        """
        Проверка подписи callback от LiqPay

        Args:
            data: Base64 encoded JSON данные
            signature: Подпись от LiqPay

        Returns:
            Dict с данными callback или None если подпись неверна
        """

        # Проверяем подпись
        expected_signature = self._generate_signature(data)

        if signature != expected_signature:
            logger.error("Неверная подпись LiqPay callback")
            return None

        # Декодируем данные
        try:
            decoded_data = base64.b64decode(data).decode('utf-8')
            callback_data = json.loads(decoded_data)

            logger.info(f"Получен callback для заказа {callback_data.get('order_id')}")

            return callback_data

        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Ошибка декодирования callback данных: {e}")
            return None

    def is_payment_successful(self, callback_data: Dict) -> bool:
        """
        Проверка успешности платежа

        Args:
            callback_data: Данные из callback

        Returns:
            True если платеж успешен
        """
        status = callback_data.get('status')

        # success - успешный платеж
        # sandbox - тестовый платеж (для разработки)
        return status in ['success', 'sandbox']

    def get_payment_status(self, callback_data: Dict) -> str:
        """
        Получение статуса платежа

        Возможные статусы:
        - success: успешный платеж
        - failure: неуспешный платеж
        - processing: платеж обрабатывается
        - sandbox: тестовый платеж
        - reversed: платеж возвращен
        """
        return callback_data.get('status', 'unknown')


def get_liqpay_service() -> LiqPayService:
    """Фабрика для получения экземпляра сервиса"""
    return LiqPayService()