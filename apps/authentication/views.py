from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import get_random_string
from apps.users.models import User, EmailVerificationToken, PhoneVerificationToken, LoginAttempt, KYCDocument
from apps.users.serializers import (
    UserRegistrationSerializer, LoginSerializer, EmailVerificationSerializer,
    PhoneVerificationSerializer, ProfileSerializer, ChangePasswordSerializer,
    RoleSwitchSerializer
)
from apps.core.utils import generate_verification_token, send_sms_verification
from apps.plans.models import Plan
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # Create email verification token
        token = generate_verification_token()
        EmailVerificationToken.objects.create(
            user=user,
            token=token,
            expires_at=timezone.now() + timezone.timedelta(hours=24)
        )
        
        # Send verification email
        send_mail(
            subject='Verify your email',
            message=f'Your verification token: {token}',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        return Response({
            'message': 'User created successfully. Please verify your email.',
            'user_id': user.id,
            'user_type': user.user_type
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        device_fingerprint = serializer.validated_data['device_fingerprint']
        
        # Record login attempt
        LoginAttempt.objects.create(
            user=user,
            email=user.email,
            ip_address=request.META.get('REMOTE_ADDR'),
            device_fingerprint=device_fingerprint,
            success=True
        )
        
        # Update last login info
        user.last_login_ip = request.META.get('REMOTE_ADDR')
        user.last_login_device = device_fingerprint
        user.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'user_type': user.user_type,
                'active_role': user.active_role,
                'is_account_activated': user.is_account_activated,
                'can_access_client_features': user.can_access_client_features(),
                'can_access_freelancer_features': user.can_access_freelancer_features()
            }
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout_view(request):
    logout(request)
    return Response({'message': 'Logged out successfully'})

@api_view(['POST'])
@permission_classes([AllowAny])
def email_verification_view(request):
    serializer = EmailVerificationSerializer(data=request.data)
    if serializer.is_valid():
        try:
            token_obj = EmailVerificationToken.objects.get(token=serializer.validated_data['token'])
            if token_obj.is_expired():
                return Response({'error': 'Token expired'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = token_obj.user
            user.is_email_verified = True
            user.save()
            
            token_obj.delete()
            
            return Response({'message': 'Email verified successfully'})
        except EmailVerificationToken.DoesNotExist:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def phone_verification_view(request):
    serializer = PhoneVerificationSerializer(data=request.data)
    if serializer.is_valid():
        try:
            token_obj = PhoneVerificationToken.objects.get(
                token=serializer.validated_data['token'],
                phone_number=serializer.validated_data['phone_number']
            )
            if token_obj.is_expired():
                return Response({'error': 'Token expired'}, status=status.HTTP_400_BAD_REQUEST)
            
            user = token_obj.user
            user.is_phone_verified = True
            user.phone_number = token_obj.phone_number
            user.save()
            
            token_obj.delete()
            
            return Response({'message': 'Phone number verified successfully'})
        except PhoneVerificationToken.DoesNotExist:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def request_phone_verification_view(request):
    phone_number = request.data.get('phone_number')
    if not phone_number:
        return Response({'error': 'Phone number is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(phone_number=phone_number)
        token = get_random_string(6, '0123456789')
        
        PhoneVerificationToken.objects.create(
            user=user,
            phone_number=phone_number,
            token=token,
            expires_at=timezone.now() + timezone.timedelta(minutes=10)
        )
        
        # Send SMS verification (implement based on your SMS provider)
        send_sms_verification(phone_number, token)
        
        return Response({'message': 'Verification code sent'})
    except User.DoesNotExist:
        return Response({'error': 'User with this phone number does not exist'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def switch_role_view(request):
    serializer = RoleSwitchSerializer(data=request.data)
    if serializer.is_valid():
        new_role = serializer.validated_data['new_role']
        
        if new_role == 'client' and not request.user.can_access_client_features():
            return Response({'error': 'No active client subscription'}, status=status.HTTP_400_BAD_REQUEST)
        
        if new_role == 'freelancer' and not request.user.can_access_freelancer_features():
            return Response({'error': 'No active freelancer subscription'}, status=status.HTTP_400_BAD_REQUEST)
        
        request.user.active_role = new_role
        request.user.save()
        
        return Response({
            'message': 'Role switched successfully',
            'new_role': new_role
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def upload_kyc_document_view(request):
    document_type = request.data.get('document_type')
    document_file = request.FILES.get('document_file')
    
    if not document_type or not document_file:
        return Response({'error': 'Document type and file are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate file type
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
    file_extension = document_file.name.split('.')[-1].lower()
    if f'.{file_extension}' not in allowed_extensions:
        return Response({'error': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)
    
    kyc_document = KYCDocument.objects.create(
        user=request.user,
        document_type=document_type,
        document_file=document_file
    )
    
    return Response({
        'message': 'KYC document uploaded successfully',
        'document_id': kyc_document.id
    })