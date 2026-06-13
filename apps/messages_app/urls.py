from django.urls import path
from . import views

app_name = 'messages_app'
urlpatterns = [
    path('send/', views.send_message, name='send'),
    path('inbox/', views.inbox, name='inbox'),
    path('<int:pk>/', views.message_detail, name='detail'),
    path('<int:pk>/reply/', views.message_reply, name='reply'),
]
