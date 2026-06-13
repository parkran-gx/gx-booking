from django.urls import path
from . import views

app_name = 'classes'
urlpatterns = [
    path('', views.class_list, name='list'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('calendar/', views.calendar_view, name='calendar'),
]
