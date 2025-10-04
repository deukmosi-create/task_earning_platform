from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/', views.email_verification_view, name='verify_email'),
    path('verify-phone/', views.phone_verification_view, name='verify_phone'),
    path('request-phone-verification/', views.request_phone_verification_view, name='request_phone_verification'),
    path('switch-role/', views.switch_role_view, name='switch_role'),
    path('kyc/upload/', views.upload_kyc_document_view, name='upload_kyc_document'),
]