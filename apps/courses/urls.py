from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('catalog/', views.courses_catalog, name='course_catalog'),
    path('my/', views.my_courses, name='my_courses'),
    path('<slug:slug>/', views.course_detail, name='course_detail'),
    path('<slug:slug>/pay/', views.initiate_payment, name='initiate_payment'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('payment/result/<str:order_id>/', views.payment_result, name='payment_result'),
    path('<slug:course_slug>/lesson/<slug:lesson_slug>/', views.lesson_detail, name='lesson_detail'),
]