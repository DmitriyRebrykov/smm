from django.urls import path
from . import views

app_name = 'courses'

urlpatterns = [
    path('lesson', views.course, name='course'),
]