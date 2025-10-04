from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.users.views import welcome_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Allauth URLs (add this)
    path('accounts/', include('allauth.urls')),
    
    # Welcome page
    path('', welcome_view, name='welcome'),
    
    # Authentication URLs
    path('api/auth/', include('apps.authentication.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User profile URLs
    path('api/users/', include('apps.users.urls')),
    
    # Task URLs
    path('api/tasks/', include('apps.tasks.urls')),
    
    # Freelancer URLs
    path('api/freelancers/', include('apps.freelancers.urls')),
    
    # Client URLs
    path('api/clients/', include('apps.clients.urls')),
    
    # Document URLs
    path('api/documents/', include('apps.documents.urls')),
    
    # Plan URLs
    path('api/plans/', include('apps.plans.urls')),
    
    # Payment URLs
    path('api/payments/', include('apps.payments.urls')),
    
    # Wallet URLs
    path('api/wallets/', include('apps.wallets.urls')),
    
    # Notification URLs
    path('api/notifications/', include('apps.notifications.urls')),
    
    # Admin panel URLs
    path('api/admin/', include('apps.admin_panel.urls')),
    
    # Dashboard URLs (add this)
    path('api/dashboard/', include('apps.dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)