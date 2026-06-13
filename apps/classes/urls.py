from django.urls import path
from . import views

app_name = 'classes'
urlpatterns = [
    path('', views.landing, name='landing'),
    path('classes/', views.class_list, name='list'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('qr/', views.qr_view, name='qr_view'),
    path('qr/download/', views.qr_generate, name='qr_generate'),
]
