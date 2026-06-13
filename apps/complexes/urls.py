from django.urls import path
from . import views

app_name = 'complexes'
urlpatterns = [
    path('', views.complex_list, name='list'),
    path('create/', views.complex_create, name='create'),
    path('<int:pk>/edit/', views.complex_edit, name='edit'),
]
