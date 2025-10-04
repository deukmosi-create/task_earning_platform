from django.urls import path
from . import views

urlpatterns = [
    path('stats/', views.dashboard_stats, name='dashboard_stats'),
    path('users/', views.user_list_api, name='user_list_api'),
    path('tasks/', views.task_list_api, name='task_list_api'),
]