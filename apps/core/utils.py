from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
import hashlib
import logging

logger = logging.getLogger(__name__)

def generate_verification_token():
    """Generate a secure verification token"""
    return get_random_string(32)

def send_sms_verification(phone_number, token):
    """Send SMS verification (implement based on your SMS provider)"""
    # This is a placeholder - implement with your SMS provider (Twilio, etc.)
    logger.info(f"SMS verification sent to {phone_number}: {token}")
    return True

def generate_device_fingerprint(request):
    """Generate a unique device fingerprint"""
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    ip_address = request.META.get('REMOTE_ADDR', '')
    accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    
    fingerprint_data = f"{user_agent}{ip_address}{accept_language}"
    return hashlib.sha256(fingerprint_data.encode()).hexdigest()

def send_notification_email(user, subject, message):
    """Send notification email"""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {user.email}: {str(e)}")
        return False

def validate_kyc_document(document_path):
    """Validate KYC document (implement based on your requirements)"""
    # This would typically involve OCR and document verification
    # For now, return True as a placeholder
    return True

def validate_file_type(file_path, allowed_extensions):
    """Validate file type based on extension only (Windows-compatible)"""
    try:
        import os
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension not in allowed_extensions:
            return False, f"Invalid file extension: {file_extension}"
        
        # Check file size (max 5MB)
        file_size = os.path.getsize(file_path)
        if file_size > 5 * 1024 * 1024:  # 5MB
            return False, "File too large"
        
        return True, "Valid"
    except Exception as e:
        logger.error(f"File validation error: {str(e)}")
        return False, str(e)