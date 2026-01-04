from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.index, name='index'),
    path('cases', views.cases, name='cases'),
    path('submit-contact/', views.submit_contact_form, name='submit_contact'),
]