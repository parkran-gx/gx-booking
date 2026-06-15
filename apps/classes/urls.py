from django.urls import path
from . import views

app_name = 'classes'
urlpatterns = [
    path('', views.landing, name='landing'),
    path('classes/', views.class_list, name='list'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/schedule/create/', views.schedule_create, name='schedule_create'),
    path('calendar/schedule/<int:schedule_id>/edit/', views.schedule_edit, name='schedule_edit'),
    path('calendar/session/<int:session_id>/', views.session_edit, name='session_edit'),
    path('calendar/session/<int:session_id>/attendance/', views.attendance_view, name='attendance'),
    path('my-attendance/', views.my_attendance, name='my_attendance'),
    path('class-manage/', views.class_manage, name='manage'),
    path('class-manage/create/', views.class_create, name='class_create'),
    path('class-manage/<int:class_id>/edit/', views.class_edit, name='class_edit'),
    path('manual/', views.admin_manual, name='manual'),
    path('my-calendar/', views.my_calendar, name='my_calendar'),
    path('qr/', views.qr_view, name='qr_view'),
    path('qr/download/', views.qr_generate, name='qr_generate'),
]
