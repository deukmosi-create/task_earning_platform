from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('users/', views.user_management_view, name='user_management'),
    path('users/<int:user_id>/status/', views.update_user_status_view, name='update_user_status'),
    path('tasks/', views.task_management_view, name='task_management'),
    path('transactions/', views.transaction_overview_view, name='transaction_overview'),
    path('fraud/', views.fraud_detection_view, name='fraud_detection'),
]