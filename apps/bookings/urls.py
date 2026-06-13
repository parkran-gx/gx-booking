from django.urls import path
from . import views

app_name = 'bookings'
urlpatterns = [
    path('book/<int:class_id>/', views.book_class, name='book'),
    path('confirm/<int:booking_id>/', views.booking_confirm, name='confirm'),
    path('cancel-request/<int:booking_id>/', views.cancel_request, name='cancel_request'),
    path('check/', views.booking_check, name='check'),
    path('admin/list/<int:class_id>/', views.admin_booking_list, name='admin_list'),
    path('admin/attendance/<int:session_id>/', views.admin_attendance, name='admin_attendance'),
    path('admin/export/<int:class_id>/', views.export_booking_list, name='export'),
    path('private-lesson/', views.private_lesson_request, name='private_lesson'),
]
