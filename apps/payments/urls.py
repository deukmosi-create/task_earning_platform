from django.urls import path
from . import views

urlpatterns = [
    # Add basic URL patterns for payments
    path('deposit/', views.create_deposit_view, name='create_deposit'),
    path('webhook/stripe/', views.webhook_stripe_view, name='stripe_webhook'),
    path('withdrawal/', views.create_withdrawal_view, name='create_withdrawal'),
    path('methods/', views.user_payment_methods_view, name='payment_methods'),
    path('methods/add/', views.add_payment_method_view, name='add_payment_method'),
]