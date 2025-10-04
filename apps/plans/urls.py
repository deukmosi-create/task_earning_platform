from django.urls import path
from . import views

urlpatterns = [
    # Add basic URL patterns for plans
    path('', views.plan_list_view, name='plan_list'),
    path('upgrade/', views.upgrade_plan_view, name='upgrade_plan'),
    path('my-plan/', views.user_plan_view, name='user_plan'),
]