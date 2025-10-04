from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, EmailVerificationToken, PhoneVerificationToken, KYCDocument

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'active_role', 'is_active', 'is_email_verified', 'is_phone_verified', 'is_kyc_verified', 'date_joined')
    list_filter = ('user_type', 'active_role', 'is_active', 'is_email_verified', 'is_phone_verified', 'is_kyc_verified', 'date_joined')
    search_fields = ('username', 'email', 'phone_number')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('user_type', 'active_role', 'current_freelancer_plan', 'current_client_plan', 
                      'device_fingerprint', 'is_phone_verified', 'is_kyc_verified', 
                      'is_account_activated', 'total_earnings', 'total_deposits', 
                      'total_withdrawals', 'referral_code', 'referred_by', 'last_login_ip', 
                      'last_login_device')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {
            'fields': ('user_type', 'active_role', 'email', 'phone_number', 'device_fingerprint')
        }),
    )

@admin.register(EmailVerificationToken)
class EmailVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'expires_at', 'created_at']
    readonly_fields = ['token', 'created_at']

@admin.register(PhoneVerificationToken)
class PhoneVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'token', 'expires_at', 'created_at']
    readonly_fields = ['token', 'created_at']

@admin.register(KYCDocument)
class KYCDocumentAdmin(admin.ModelAdmin):
    list_display = ['user', 'document_type', 'status', 'uploaded_at', 'reviewed_at']
    list_filter = ['document_type', 'status', 'uploaded_at']
    readonly_fields = ['uploaded_at', 'reviewed_at']