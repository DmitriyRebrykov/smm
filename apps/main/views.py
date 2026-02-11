from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import ContactRequest
from .utils import send_telegram_notification
import logging

logger = logging.getLogger(__name__)


def index(request):
    return render(request, 'main/main.html')

def cases(request):
    return render(request, 'main/cases.html')

def reviews(request):
    return render(request, 'main/reviews.html')

@require_http_methods(["POST"])
def submit_contact_form(request):
    try:
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        service = request.POST.get('service', '')
        message = request.POST.get('message', '').strip()
        
        if not name or not email:
            return JsonResponse({
                'success': False,
                'error': 'Пожалуйста, заполните обязательные поля (Имя и Email)'
            }, status=400)
        
        contact_request = ContactRequest.objects.create(
            name=name,
            email=email,
            service=service,
            message=message
        )
        
        logger.info(f"Создана заявка #{contact_request.id}")
        
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

@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('main:index')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()
        name = request.POST.get('name', '').strip()

        errors = []

        if not email:
            errors.append('Email обязателен')
        elif not '@' in email:
            errors.append('Некорректный email')

        if not password:
            errors.append('Пароль обязателен')
        elif len(password) < 6:
            errors.append('Пароль должен быть минимум 6 символов')

        if password != password_confirm:
            errors.append('Пароли не совпадают')

        if not name:
            errors.append('Имя обязательно')

        if User.objects.filter(email=email).exists():
            errors.append('Пользователь с таким email уже существует')

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'main/auth/register.html', {
                'email': email,
                'name': name,
            })

        try:
            # Username = email (для простоты)
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name
            )

            login(request, user)

            logger.info(f"Зарегистрирован новый пользователь: {email}")
            messages.success(request, f'Добро пожаловать, {name}!')

            next_url = request.GET.get('next', 'main:index')
            return redirect(next_url)

        except IntegrityError:
            messages.error(request, 'Ошибка при создании пользователя. Попробуйте другой email.')
            return render(request, 'main/auth/register.html')

    return render(request, 'main/auth/register.html')


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Вход пользователя"""

    if request.user.is_authenticated:
        return redirect('main:index')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '').strip()

        if not email or not password:
            messages.error(request, 'Заполните все поля')
            return render(request, 'main/auth/login.html', {'email': email})

        # Пытаемся авторизовать
        # Username = email (так как мы используем email как username)
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            logger.info(f"Пользователь вошел: {email}")

            # Редирект на страницу, откуда пришли, или на главную
            next_url = request.GET.get('next') or request.POST.get('next', '/')
            messages.success(request, f'Добро пожаловать, {user.first_name or user.username}!')
            return redirect(next_url)
        else:
            messages.error(request, 'Неверный email или пароль')
            return render(request, 'main/auth/login.html', {'email': email})

    return render(request, 'main/auth/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы')
    return redirect('main:index')


def profile_view(request):

    if not request.user.is_authenticated:
        messages.info(request, 'Войдите для доступа к профилю')
        return redirect('main:login')

    from apps.courses.models import CourseAccess, Purchase

    accesses = CourseAccess.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('course')

    purchases = Purchase.objects.filter(
        user=request.user
    ).select_related('course').order_by('-created_at')[:10]

    return render(request, 'main/auth/profile.html', {
        'accesses': accesses,
        'purchases': purchases,
    })