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

from .models import Course, CourseAccess, Purchase, Lesson
from .services.liqpay_service import get_liqpay_service
import uuid
import logging

logger = logging.getLogger(__name__)


def courses_catalog(request):
    courses = Course.objects.filter(is_active=True).order_by('-created_at')

    purchased_ids = []
    if request.user.is_authenticated:
        purchased_ids = CourseAccess.objects.filter(
            user=request.user,
            is_active=True
        ).values_list('course_id', flat=True)

    context = {
        'courses': courses,
        'purchased_ids': purchased_ids,
    }
    return render(request, 'courses/course_catalog.html', context)

@login_required
def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug, is_active=True)

    try:
        access = CourseAccess.objects.get(user=request.user, course=course)
        has_access = access.has_access()
    except CourseAccess.DoesNotExist:
        has_access = False

    if has_access:
        lessons = course.lessons.all()
        return render(request, 'courses/course_content.html', {
            'course': course,
            'lessons': lessons,
            'access': access,
        })

    return render(request, 'courses/course_payment.html', {
        'course': course,
    })


@login_required
@require_POST
def initiate_payment(request, slug):
    course = get_object_or_404(Course, slug=slug, is_active=True)

    has_access = CourseAccess.objects.filter(
        user=request.user,
        course=course,
        is_active=True
    ).exists()

    if has_access:
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
            purchase.mark_as_paid()
            logger.info(f"Платеж {order_id} успешно обработан")
        else:
            logger.warning(f"Платеж {order_id} имеет статус: {payment_status}")

        purchase.save()

    return HttpResponse('OK')


@login_required
def payment_result(request, order_id):
    purchase = get_object_or_404(Purchase, order_id=order_id, user=request.user)

    context = {
        'purchase': purchase,
        'course': purchase.course,
    }

    if purchase.status == 'success':
        messages.success(request, 'Оплата прошла успешно! Добро пожаловать на курс.')
        return redirect('courses:course_detail', slug=purchase.course.slug)

    elif purchase.status == 'failure':
        messages.error(request, 'Оплата не прошла. Попробуйте еще раз.')
        return render(request, 'courses/payment_failed.html', context)

    else:
        messages.info(request, 'Платеж обрабатывается. Подождите немного.')
        return render(request, 'courses/payment_pending.html', context)


@login_required
def lesson_detail(request, course_slug, lesson_slug):
    course = get_object_or_404(Course, slug=course_slug, is_active=True)
    lesson = get_object_or_404(Lesson, course=course, slug=lesson_slug)

    if not lesson.is_free:
        try:
            access = CourseAccess.objects.get(user=request.user, course=course)
            if not access.has_access():
                messages.error(request, 'У вас нет доступа к этому уроку')
                return redirect('courses:course_detail', slug=course_slug)
        except CourseAccess.DoesNotExist:
            messages.error(request, 'Оплатите курс для доступа к урокам')
            return redirect('courses:course_detail', slug=course_slug)

    all_lessons = course.lessons.all()

    return render(request, 'courses/lesson.html', {
        'course': course,
        'lesson': lesson,
        'all_lessons': all_lessons,
    })


@login_required
def my_courses(request):
    accesses = CourseAccess.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('course')

    return render(request, 'courses/my_courses.html', {
        'accesses': accesses,
    })


def course(request):
    return redirect('main:index')