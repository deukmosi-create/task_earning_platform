from django.urls import path
from . import views

urlpatterns = [
    path('', views.task_list_api, name='task_list_api'),
    path('<int:task_id>/', views.task_detail_api, name='task_detail_api'),
    path('list/', views.task_list_view, name='task_list_view'),
    path('assign/<int:task_id>/', views.assign_task_view, name='assign_task_view'),
    path('submit/<int:assignment_id>/', views.submit_task_view, name='submit_task_view'),
    path('assignments/', views.user_assignments_view, name='user_assignments_view'),
    path('review/<int:submission_id>/', views.admin_review_submission, name='admin_review_submission'),
    path('simulate/', views.create_simulated_task_view, name='create_simulated_task_view'),
    path('logs/<int:task_id>/', views.task_activity_logs_view, name='task_activity_logs_view'),
]