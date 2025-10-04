from rest_framework import serializers
from .models import Deposit, Withdrawal, PaymentMethod

class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = '__all__'
        read_only_fields = ['user', 'transaction_id', 'status', 'created_at', 'updated_at']

class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = '__all__'
        read_only_fields = ['user', 'transaction_id', 'status', 'created_at', 'processed_at']

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class CreateDepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method = serializers.CharField()

class CreateWithdrawalSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    payment_method_id = serializers.IntegerField()
    account_details = serializers.JSONField()