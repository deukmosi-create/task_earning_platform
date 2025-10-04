# Copy and paste the following code into apps/clients/urls.py:
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.client_dashboard_view, name='client_dashboard'),
    path('tasks/', views.client_tasks_view, name='client_tasks'),
    path('documents/', views.client_documents_view, name='client_documents'),
    path('activate/', views.activate_client_account_view, name='activate_client_account'),
]