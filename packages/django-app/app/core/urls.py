from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('auth/login/', views.login, name='login'),
    path('auth/register/', views.register, name='register'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/me/', views.me, name='me'),
]