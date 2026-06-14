from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_edit, name='profile_edit'),
    path('password/change/', views.password_change, name='password_change'),
    path('password/reset/', views.password_reset_request, name='password_reset'),
    path('password/reset/confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    path('members/', views.member_manage, name='member_manage'),
]
