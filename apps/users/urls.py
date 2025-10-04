from django.urls import path
from . import views

urlpatterns = [
    path('', views.user_list_api, name='user_list_api'),
    path('<int:user_id>/', views.user_detail_api, name='user_detail_api'),
    path('<int:user_id>/status/', views.update_user_status_api, name='update_user_status_api'),
    path('profile/', views.profile_view, name='profile_view'),
    path('change-password/', views.change_password_view, name='change_password_view'),
]