from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from django.db.models import Q

from .models import Course, CourseAccess, Purchase, Lesson, LessonProgress, LessonSubmission
from .services.liqpay_service import get_liqpay_service
import uuid
import logging

logger = logging.getLogger(__name__)


def courses_catalog(request):
    courses = Course.objects.filter(is_active=True).order_by('-created_at')

    purchased_ids = set()
    if request.user.is_authenticated:
        purchased_ids = set(
            CourseAccess.objects.filter(
                user=request.user,
                is_active=True,
            ).values_list('course_id', flat=True)
        )
        # Дополнительно фильтруем — исключаем истёкшие (expires_at в прошлом)
        expired_ids = set(
            CourseAccess.objects.filter(
                user=request.user,
                is_active=True,
                expires_at__isnull=False,
                expires_at__lt=timezone.now(),
            ).values_list('course_id', flat=True)
        )
        purchased_ids -= expired_ids

    return render(request, 'courses/course_catalog.html', {
        'courses': courses,
        'purchased_ids': purchased_ids,
    })


@login_required
def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug, is_active=True)
    has_access = CourseAccess.user_has_access(request.user, course)

    if has_access:
        lessons = course.lessons.all()
        progress_pct = LessonProgress.get_course_progress(request.user, course)
        completed_ids = LessonProgress.get_completed_ids(request.user, course)

        # Первый незавершённый урок для кнопки «Продолжить»
        next_lesson = next(
            (lesson for lesson in lessons if lesson.id not in completed_ids),
            None
        )

        return render(request, 'courses/course_content.html', {
            'course': course,
            'lessons': lessons,
            'progress_pct': progress_pct,
            'completed_ids': completed_ids,
            'next_lesson': next_lesson,
        })

    return render(request, 'courses/course_payment.html', {
        'course': course,
    })


@login_required
@require_POST
def initiate_payment(request, slug):
    course = get_object_or_404(Course, slug=slug, is_active=True)

    if CourseAccess.user_has_access(request.user, course):
        messages.info(request, 'У вас уже есть доступ к этому курсу')
        return redirect('courses:course_detail', slug=slug)

    order_id = f"ORDER-{uuid.uuid4().hex[:12].upper()}"

    purchase = Purchase.objects.create(
        user=request.user,
        course=course,
        amount=course.price,
        currency=course.currency,
        order_id=order_id,
        customer_email=request.user.email,
        customer_name=request.user.get_full_name() or request.user.username,
        status='pending',
    )

    liqpay = get_liqpay_service()

    result_url = request.build_absolute_uri(
        reverse('courses:payment_result', kwargs={'order_id': order_id})
    )
    server_url = request.build_absolute_uri(
        reverse('courses:payment_callback')
    )

    payment_data = liqpay.create_payment_form_data(
        order_id=order_id,
        amount=float(course.price),
        description=f"Оплата курса: {course.title}",
        result_url=result_url,
        server_url=server_url,
        currency=course.currency,
        customer=request.user.email,
    )

    logger.info(f"Инициирован платеж {order_id} для пользователя {request.user.email}")

    return render(request, 'courses/payment_redirect.html', {
        'payment_data': payment_data,
        'liqpay_api_url': liqpay.API_URL,
        'course': course,
        'order_id': order_id,
    })


@csrf_exempt
@require_POST
def payment_callback(request):
    data = request.POST.get('data')
    signature = request.POST.get('signature')

    if not data or not signature:
        logger.error("Callback без данных или подписи")
        return HttpResponse(status=400)

    liqpay = get_liqpay_service()
    callback_data = liqpay.verify_callback(data, signature)

    if not callback_data:
        logger.error("Неверная подпись LiqPay callback")
        return HttpResponse(status=400)

    order_id = callback_data.get('order_id')

    try:
        purchase = Purchase.objects.select_for_update().get(order_id=order_id)
    except Purchase.DoesNotExist:
        logger.error(f"Заказ {order_id} не найден")
        return HttpResponse(status=404)

    with transaction.atomic():
        purchase.callback_data = callback_data
        purchase.payment_id = callback_data.get('payment_id', '')
        purchase.liqpay_order_id = callback_data.get('liqpay_order_id', '')

        payment_status = liqpay.get_payment_status(callback_data)

        status_mapping = {
            'success': 'success',
            'sandbox': 'success',
            'failure': 'failure',
            'error': 'failure',
            'reversed': 'reversed',
            'processing': 'processing',
        }

        new_status = status_mapping.get(payment_status, 'processing')
        purchase.status = new_status

        if liqpay.is_payment_successful(callback_data):
            # mark_as_paid выдаёт вечный доступ и отправляет email
            purchase.mark_as_paid()
            logger.info(f"Платеж {order_id} успешно обработан")
        else:
            purchase.save()
            logger.warning(f"Платеж {order_id} имеет статус: {payment_status}")

    return HttpResponse('OK')


@login_required
def payment_result(request, order_id):
    purchase = get_object_or_404(Purchase, order_id=order_id, user=request.user)

    if purchase.status == 'success':
        messages.success(request, 'Оплата прошла успешно! Добро пожаловать на курс.')
        return redirect('courses:course_detail', slug=purchase.course.slug)

    elif purchase.status == 'failure':
        messages.error(request, 'Оплата не прошла. Попробуйте ещё раз.')
        return render(request, 'courses/payment_failed.html', {
            'purchase': purchase,
            'course': purchase.course,
        })

    else:
        messages.info(request, 'Платёж обрабатывается. Подождите немного.')
        return render(request, 'courses/payment_pending.html', {
            'purchase': purchase,
            'course': purchase.course,
        })


@login_required
def lesson_detail(request, course_slug, lesson_slug):
    course = get_object_or_404(Course, slug=course_slug, is_active=True)
    lesson = get_object_or_404(Lesson, course=course, slug=lesson_slug)

    # Бесплатные уроки доступны всем авторизованным пользователям
    if not lesson.is_free:
        if not CourseAccess.user_has_access(request.user, course):
            messages.error(request, 'Оплатите курс для доступа к урокам')
            return redirect('courses:course_detail', slug=course_slug)

    all_lessons = course.lessons.all()

    progress_pct = LessonProgress.get_course_progress(request.user, course)
    completed_ids = LessonProgress.get_completed_ids(request.user, course)

    lesson_progress, _ = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )

    lessons_list = list(all_lessons)
    current_index = next((i for i, l in enumerate(lessons_list) if l.id == lesson.id), None)
    prev_lesson = lessons_list[current_index - 1] if current_index and current_index > 0 else None
    next_lesson = lessons_list[current_index + 1] if current_index is not None and current_index < len(lessons_list) - 1 else None

    submissions = LessonSubmission.objects.filter(
        user=request.user,
        lesson=lesson
    ).order_by('-created_at')

    return render(request, 'courses/lesson.html', {
        'course': course,
        'lesson': lesson,
        'lessons': all_lessons,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'progress_pct': progress_pct,
        'completed_ids': completed_ids,
        'lesson_progress': lesson_progress,
        'submissions': submissions,
    })


@login_required
@require_POST
def complete_lesson(request, course_slug, lesson_slug):
    """AJAX: отметить урок как завершённый"""
    course = get_object_or_404(Course, slug=course_slug, is_active=True)
    lesson = get_object_or_404(Lesson, course=course, slug=lesson_slug)

    if not lesson.is_free and not CourseAccess.user_has_access(request.user, course):
        return JsonResponse({'error': 'Нет доступа'}, status=403)

    progress, _ = LessonProgress.objects.get_or_create(
        user=request.user,
        lesson=lesson
    )
    progress.mark_completed()

    return JsonResponse({
        'success': True,
        'lesson_id': lesson.id,
        'progress_pct': LessonProgress.get_course_progress(request.user, course),
        'message': 'Урок завершён!'
    })


@login_required
@require_POST
def submit_homework(request, course_slug, lesson_slug):
    """Загрузка домашней работы"""
    course = get_object_or_404(Course, slug=course_slug, is_active=True)
    lesson = get_object_or_404(Lesson, course=course, slug=lesson_slug)

    if not lesson.is_free and not CourseAccess.user_has_access(request.user, course):
        messages.error(request, 'Нет доступа к уроку')
        return redirect('courses:course_detail', slug=course_slug)

    uploaded_file = request.FILES.get('submission_file')
    comment = request.POST.get('comment', '').strip()

    if not uploaded_file:
        messages.error(request, 'Выберите файл для загрузки')
        return redirect('courses:lesson_detail', course_slug=course_slug, lesson_slug=lesson_slug)

    import os
    ALLOWED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp',
                          '.mp4', '.mov', '.avi', '.mkv', '.webm'}
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        messages.error(request, f'Формат "{ext}" не поддерживается.')
        return redirect('courses:lesson_detail', course_slug=course_slug, lesson_slug=lesson_slug)

    if uploaded_file.size > 50 * 1024 * 1024:
        messages.error(request, 'Файл слишком большой. Максимум 50 МБ.')
        return redirect('courses:lesson_detail', course_slug=course_slug, lesson_slug=lesson_slug)

    LessonSubmission.objects.create(
        user=request.user,
        lesson=lesson,
        file=uploaded_file,
        comment=comment,
    )

    messages.success(request, 'Работа отправлена на проверку!')
    return redirect('courses:lesson_detail', course_slug=course_slug, lesson_slug=lesson_slug)


@login_required
def my_courses(request):
    accesses = CourseAccess.objects.filter(
        user=request.user,
        is_active=True,
    ).select_related('course').filter(
        # Исключаем истёкшие временные доступы
        Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
    )

    courses_with_progress = [
        {
            'access': access,
            'progress': LessonProgress.get_course_progress(request.user, access.course),
        }
        for access in accesses
    ]

    return render(request, 'courses/my_courses.html', {
        'accesses': accesses,
        'courses_with_progress': courses_with_progress,
    })


def course(request):
    return redirect('main:index')