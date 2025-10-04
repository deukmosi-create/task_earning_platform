from django.urls import path
from . import views

urlpatterns = [
    path('', views.wallet_view, name='wallet'),
    path('transactions/', views.transaction_history_view, name='transaction_history'),
    path('balance/', views.balance_view, name='balance'),
]