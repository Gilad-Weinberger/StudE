from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('', views.Chatbot, name='chatbot'),
    path('handle_message/', views.handle_message, name='handle_message'),
]