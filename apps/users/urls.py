from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # Авторизация
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Профиль
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),

    # Курсы и покупки
    path('my-courses/', views.my_courses_view, name='my_courses'),
    path('purchases/', views.purchases_history_view, name='purchases'),
]