from django.urls import path
from . import views

urlpatterns = [
    path('', views.notifications_view, name='notifications'),
    path('mark-read/<int:notification_id>/', views.mark_notification_read_view, name='mark_notification_read'),
    path('unread-count/', views.unread_notifications_count_view, name='unread_notifications_count'),
    path('messages/', views.messages_view, name='messages'),
    path('messages/send/', views.send_message_view, name='send_message'),
    path('messages/reply/<int:message_id>/', views.reply_message_view, name='reply_message'),
]