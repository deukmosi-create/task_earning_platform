from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, EmailVerificationToken, PhoneVerificationToken
from phonenumber_field.serializerfields import PhoneNumberField
import re

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    phone_number = PhoneNumberField(required=False, allow_blank=True)
    user_type = serializers.ChoiceField(choices=['freelancer', 'client'])
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password_confirm', 'phone_number', 
                 'device_fingerprint', 'user_type', 'active_role']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        
        # Check for duplicate email/phone/device
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("Email already exists")
        
        if attrs.get('phone_number') and User.objects.filter(phone_number=attrs['phone_number']).exists():
            raise serializers.ValidationError("Phone number already exists")
        
        if attrs.get('device_fingerprint') and User.objects.filter(device_fingerprint=attrs['device_fingerprint']).exists():
            raise serializers.ValidationError("Device already registered")
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        device_fingerprint = validated_data.pop('device_fingerprint', None)
        user_type = validated_data.pop('user_type', 'freelancer')
        
        user = User.objects.create_user(**validated_data)
        user.user_type = user_type
        user.active_role = user_type
        if device_fingerprint:
            user.device_fingerprint = device_fingerprint
        user.save()
        
        return user

class LoginSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField()
    password = serializers.CharField()
    device_fingerprint = serializers.CharField()
    
    def validate(self, attrs):
        email_or_phone = attrs.get('email_or_phone')
        password = attrs.get('password')
        device_fingerprint = attrs.get('device_fingerprint')
        
        # Check if it's an email or phone number
        if '@' in email_or_phone:
            user = authenticate(email=email_or_phone, password=password)
        else:
            try:
                user = authenticate(phone_number=email_or_phone, password=password)
            except:
                user = None
        
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        
        if not user.is_email_verified:
            raise serializers.ValidationError("Email not verified")
        
        if user.phone_number and not user.is_phone_verified:
            raise serializers.ValidationError("Phone number not verified")
        
        if user.device_fingerprint and user.device_fingerprint != device_fingerprint:
            raise serializers.ValidationError("Device not registered")
        
        attrs['user'] = user
        attrs['device_fingerprint'] = device_fingerprint
        return attrs

class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()

class PhoneVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()
    phone_number = PhoneNumberField()

class ProfileSerializer(serializers.ModelSerializer):
    can_access_client_features = serializers.SerializerMethodField()
    can_access_freelancer_features = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'phone_number', 'user_type', 'active_role',
                 'current_freelancer_plan', 'current_client_plan', 'is_phone_verified', 
                 'is_email_verified', 'is_kyc_verified', 'is_account_activated', 
                 'total_earnings', 'total_deposits', 'total_withdrawals', 'referral_code', 
                 'created_at', 'can_access_client_features', 'can_access_freelancer_features']
        read_only_fields = ['id', 'email', 'created_at', 'total_earnings', 'total_deposits', 'total_withdrawals']
    
    def get_can_access_client_features(self, obj):
        return obj.can_access_client_features()
    
    def get_can_access_freelancer_features(self, obj):
        return obj.can_access_freelancer_features()

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs

class RoleSwitchSerializer(serializers.Serializer):
    new_role = serializers.ChoiceField(choices=['freelancer', 'client', 'both'])