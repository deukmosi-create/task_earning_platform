from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone
from uuid import uuid4
import hashlib

class User(AbstractUser):
    USER_TYPES = [
        ('freelancer', 'Freelancer'),
        ('client', 'Client'),
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
    ]
    
    ROLE_CHOICES = [
        ('freelancer', 'Freelancer'),
        ('client', 'Client'),
        ('both', 'Both'),
    ]
    
    email = models.EmailField(unique=True)
    phone_number = PhoneNumberField(unique=True, blank=True, null=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='freelancer')
    active_role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='freelancer')
    current_freelancer_plan = models.CharField(max_length=20, default='basic')
    current_client_plan = models.CharField(max_length=20, default='basic')
    device_fingerprint = models.CharField(max_length=128, unique=True, blank=True, null=True)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_kyc_verified = models.BooleanField(default=False)
    is_account_activated = models.BooleanField(default=False)
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_deposits = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_withdrawals = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    referral_code = models.CharField(max_length=12, unique=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    last_login_device = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    # Fix reverse accessor conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',  # Changed related_name
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',  # Changed related_name
        blank=True,
    )
    
    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = self.generate_referral_code()
        super().save(*args, **kwargs)
    
    def generate_referral_code(self):
        return str(uuid4())[:12].upper()
    
    def can_access_client_features(self):
        """Check if user has active client subscription"""
        from apps.plans.models import Plan
        plan = Plan.objects.filter(name=self.current_client_plan, is_active=True).first()
        return plan is not None
    
    def can_access_freelancer_features(self):
        """Check if user has active freelancer subscription"""
        from apps.plans.models import Plan
        plan = Plan.objects.filter(name=self.current_freelancer_plan, is_active=True).first()
        return plan is not None
    
    def switch_role(self, new_role):
        """Switch between freelancer and client roles"""
        if new_role in ['freelancer', 'client', 'both']:
            self.active_role = new_role
            self.save()
            return True
        return False
    
    def __str__(self):
        return f"{self.email} - {self.user_type}"

class EmailVerificationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_expired(self):
        return timezone.now() > self.expires_at

class PhoneVerificationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = PhoneNumberField()
    token = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_expired(self):
        return timezone.now() > self.expires_at

class LoginAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    ip_address = models.GenericIPAddressField()
    device_fingerprint = models.CharField(max_length=128)
    success = models.BooleanField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']

class SessionControl(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_key = models.CharField(max_length=40)
    device_fingerprint = models.CharField(max_length=128)
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['user', 'session_key']

class KYCDocument(models.Model):
    DOCUMENT_TYPES = [
        ('id_card', 'ID Card'),
        ('passport', 'Passport'),
        ('driver_license', 'Driver License'),
        ('utility_bill', 'Utility Bill'),
        ('bank_statement', 'Bank Statement'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    document_file = models.FileField(upload_to='kyc_documents/')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.document_type}"