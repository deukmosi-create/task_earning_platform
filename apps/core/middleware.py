from django.utils import timezone
from django.http import JsonResponse
from apps.users.models import User, SessionControl
from apps.core.utils import generate_device_fingerprint
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class SessionControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Check for existing active sessions
            active_sessions = SessionControl.objects.filter(
                user=request.user,
                is_active=True
            ).exclude(session_key=request.session.session_key)
            
            if active_sessions.exists():
                # Log out other sessions
                active_sessions.update(is_active=False)
            
            # Create or update current session
            SessionControl.objects.update_or_create(
                user=request.user,
                session_key=request.session.session_key,
                defaults={
                    'device_fingerprint': generate_device_fingerprint(request),
                    'ip_address': request.META.get('REMOTE_ADDR', ''),
                    'last_activity': timezone.now(),
                    'is_active': True
                }
            )
        
        response = self.get_response(request)
        return response

class FraudDetectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Rate limiting based on IP
        ip_address = request.META.get('REMOTE_ADDR', '')
        cache_key = f'rate_limit_{ip_address}'
        
        request_count = cache.get(cache_key, 0)
        if request_count >= 100:  # 100 requests per hour
            return JsonResponse({
                'error': 'Rate limit exceeded'
            }, status=429)
        
        cache.set(cache_key, request_count + 1, 3600)  # 1 hour
        
        response = self.get_response(request)
        return response

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Implement rate limiting logic
        user = request.user
        if user.is_authenticated:
            cache_key = f'rate_limit_user_{user.id}'
            request_count = cache.get(cache_key, 0)
            
            if request_count >= 5000:  # 1000 requests per hour
                return JsonResponse({
                    'error': 'Rate limit exceeded'
                }, status=429)
            
            cache.set(cache_key, request_count + 1, 3600)
        
        response = self.get_response(request)
        return response

class SubscriptionVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check subscription for specific endpoints
        path = request.path
        
        # Check client-specific endpoints
        if path.startswith('/api/clients/') or path.startswith('/api/documents/'):
            if request.user.is_authenticated:
                if request.user.active_role not in ['client', 'both']:
                    return JsonResponse({
                        'error': 'Access denied - client role required'
                    }, status=403)
                
                if not request.user.can_access_client_features():
                    return JsonResponse({
                        'error': 'No active client subscription'
                    }, status=400)
        
        # Check freelancer-specific endpoints
        elif path.startswith('/api/freelancers/'):
            if request.user.is_authenticated:
                if request.user.active_role not in ['freelancer', 'both']:
                    return JsonResponse({
                        'error': 'Access denied - freelancer role required'
                    }, status=403)
                
                if not request.user.can_access_freelancer_features():
                    return JsonResponse({
                        'error': 'No active freelancer subscription'
                    }, status=400)
        
        response = self.get_response(request)
        return response