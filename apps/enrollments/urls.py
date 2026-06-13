from django.urls import path
from . import views

app_name = 'enrollments'
urlpatterns = [
    path('', views.enrollment_list, name='list'),
    path('register/<int:period_id>/', views.enroll, name='enroll'),
    path('cancel/<int:enrollment_id>/', views.cancel_request, name='cancel'),
    path('admin/', views.admin_period_list, name='admin_list'),
    path('admin/create/', views.admin_period_create, name='admin_create'),
    path('admin/<int:period_id>/', views.admin_period_detail, name='admin_detail'),
    path('admin/<int:period_id>/edit/', views.admin_period_edit, name='admin_edit'),
    path('admin/<int:period_id>/priority/', views.admin_priority_members, name='admin_priority'),
    path('admin/<int:period_id>/promote/<int:enrollment_id>/', views.admin_promote, name='admin_promote'),
    path('admin/<int:period_id>/cancel/<int:enrollment_id>/', views.admin_cancel, name='admin_cancel'),
    path('admin/<int:period_id>/manual/', views.admin_manual_enroll, name='admin_manual'),
    path('admin/<int:period_id>/export/', views.admin_export, name='admin_export'),
    path('admin/<int:period_id>/export-pdf/', views.admin_export_pdf, name='admin_export_pdf'),
    path('admin/<int:period_id>/export-xlsx/', views.admin_export_xlsx, name='admin_export_xlsx'),
    path('admin/<int:period_id>/office-send/', views.admin_office_send, name='admin_office_send'),
    path('admin/<int:period_id>/sync-status/', views.admin_sync_status, name='admin_sync'),
    path('admin/<int:period_id>/change-status/', views.admin_change_status, name='admin_change_status'),
]
