# Copy and paste the following code into apps/freelancers/urls.py:
from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.freelancer_dashboard_view, name='freelancer_dashboard'),
    path('earnings/', views.freelancer_earnings_view, name='freelancer_earnings'),
    path('profile/', views.freelancer_profile_view, name='freelancer_profile'),
]