from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.core.paginator import Paginator
from django.db.models import Q
from .models import User, EmailVerificationToken, PhoneVerificationToken, KYCDocument
from .serializers import UserRegistrationSerializer, ProfileSerializer, ChangePasswordSerializer
from apps.core.utils import generate_verification_token, send_sms_verification
from apps.plans.models import Plan
from apps.wallets.models import Wallet, Transaction
from apps.notifications.models import Notification
from apps.notifications.utils import send_notification
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([AllowAny])
def welcome_view(request):
    """Welcome page endpoint"""
    welcome_data = {
        'title': 'Task Earning Platform',
        'description': 'Connect with skilled freelancers or find work opportunities. Choose your role to get started.',
        'features': [
            'Secure task management',
            'Real-time payments',
            'Professional freelancers',
            'Client-friendly interface'
        ],
        'roles': {
            'freelancer': {
                'title': 'Get Started as a Freelancer',
                'description': 'Complete tasks and earn money',
                'endpoint': '/api/auth/register/?role=freelancer'
            },
            'client': {
                'title': 'Get Started to Submit Work',
                'description': 'Post tasks and get them completed',
                'endpoint': '/api/auth/register/?role=client'
            }
        }
    }
    return Response(welcome_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_list_api(request):
    """API endpoint for listing users"""
    if request.user.user_type not in ['admin', 'moderator']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    # Get query parameters
    search_term = request.GET.get('search', '')
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 10))

    # Filter users
    users = User.objects.all().order_by('-created_at')

    if search_term:
        users = users.filter(
            Q(username__icontains=search_term) |
            Q(email__icontains=search_term) |
            Q(phone_number__icontains=search_term)
        )

    # Paginate
    paginator = Paginator(users, limit)
    page_obj = paginator.get_page(page)

    # Serialize data
    user_data = []
    for user in page_obj:
        user_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'phone_number': str(user.phone_number),
            'user_type': user.user_type,
            'is_active': user.is_active,
            'is_email_verified': user.is_email_verified,
            'is_phone_verified': user.is_phone_verified,
            'is_kyc_verified': user.is_kyc_verified,
            'current_plan': user.current_plan,
            'total_earnings': float(user.total_earnings),
            'total_deposits': float(user.total_deposits),
            'total_withdrawals': float(user.total_withdrawals),
            'created_at': user.created_at.isoformat()
        })

    response_data = {
        'results': user_data,
        'count': paginator.count,
        'next': page_obj.has_next(),
        'previous': page_obj.has_previous(),
        'total_pages': paginator.num_pages
    }

    return Response(response_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_detail_api(request, user_id):
    """API endpoint for getting a specific user's details"""
    if request.user.user_type not in ['admin', 'moderator']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    try:
        user = User.objects.get(id=user_id)
        serializer = ProfileSerializer(user)
        return Response(serializer.data)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user_status_api(request, user_id):
    """API endpoint for updating a user's status"""
    if request.user.user_type not in ['admin', 'moderator']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    try:
        user = User.objects.get(id=user_id)
        action = request.data.get('action')

        if action == 'activate':
            user.is_active = True
        elif action == 'deactivate':
            user.is_active = False
        elif action == 'verify_email':
            user.is_email_verified = True
        elif action == 'verify_phone':
            user.is_phone_verified = True
        elif action == 'verify_kyc':
            user.is_kyc_verified = True
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

        user.save()
        return Response({'message': 'User status updated successfully'})

    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET', 'PUT'])
def profile_view(request):
    if request.method == 'GET':
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def change_password_view(request):
    serializer = ChangePasswordSerializer(data=request.data)
    if serializer.is_valid():
        user = request.user

        if not user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response({'message': 'Password changed successfully'})

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)