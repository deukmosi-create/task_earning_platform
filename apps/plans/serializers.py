from rest_framework import serializers
from .models import Plan, PlanUpgrade

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = '__all__'

class PlanUpgradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanUpgrade
        fields = '__all__'
        read_only_fields = ['user', 'old_plan', 'status', 'created_at']

class PlanUpgradeRequestSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    payment_method = serializers.CharField()