from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import ContactRequest
from .utils import send_telegram_notification
import logging

logger = logging.getLogger(__name__)


def index(request):
    """Главная страница"""
    return render(request, 'main/main.html')

def cases(request):
    return render(request, 'main/cases.html')


@require_http_methods(["POST"])
def submit_contact_form(request):
    """
    Обработка отправки формы контакта
    """
    try:
        # Получаем данные из формы
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        service = request.POST.get('service', '')
        message = request.POST.get('message', '').strip()
        
        # Валидация
        if not name or not email:
            return JsonResponse({
                'success': False,
                'error': 'Пожалуйста, заполните обязательные поля (Имя и Email)'
            }, status=400)
        
        # Создаем заявку
        contact_request = ContactRequest.objects.create(
            name=name,
            email=email,
            service=service,
            message=message
        )
        
        logger.info(f"Создана заявка #{contact_request.id}")
        
        # Отправляем в Telegram
        telegram_sent = send_telegram_notification(contact_request)
        
        if telegram_sent:
            logger.info(f"Заявка #{contact_request.id} успешно отправлена в Telegram")
        else:
            logger.warning(f"Заявка #{contact_request.id} сохранена, но не отправлена в Telegram")
        
        return JsonResponse({
            'success': True,
            'message': 'Спасибо за заявку! Я свяжусь с вами в ближайшее время.',
            'request_id': contact_request.id
        })
        
    except Exception as e:
        logger.error(f"Ошибка обработки формы: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': 'Произошла ошибка при отправке заявки. Попробуйте позже.'
        }, status=500)