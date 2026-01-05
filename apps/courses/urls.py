from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    # Список моих курсов
    path('my/', views.my_courses, name='my_courses'),

    # Детальная страница курса (оплата или контент)
    path('<slug:slug>/', views.course_detail, name='course_detail'),

    # Инициация платежа
    path('<slug:slug>/pay/', views.initiate_payment, name='initiate_payment'),

    # Callback от LiqPay
    path('payment/callback/', views.payment_callback, name='payment_callback'),

    # Результат платежа
    path('payment/result/<str:order_id>/', views.payment_result, name='payment_result'),

    # Урок курса
    path('<slug:course_slug>/lesson/<slug:lesson_slug>/', views.lesson_detail, name='lesson_detail'),
]