# Copy and paste the following code into apps/documents/urls.py:
from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_document_view, name='upload_document'),
    path('client/', views.client_documents_view, name='client_documents'),
    path('create-task/', views.create_task_from_document_view, name='create_task_from_document'),
]