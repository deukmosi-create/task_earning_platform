from rest_framework import serializers
from .models import Task, TaskAssignment, TaskSubmission, TaskActivityLog
from apps.plans.models import Plan
from apps.users.models import User

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ['created_by', 'current_assignments', 'created_at', 'updated_at']

class TaskAssignmentSerializer(serializers.ModelSerializer):
    task_title = serializers.CharField(source='task.title', read_only=True)
    task_description = serializers.CharField(source='task.description', read_only=True)
    task_reward = serializers.DecimalField(source='task.reward', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = TaskAssignment
        fields = '__all__'
        read_only_fields = ['user', 'status', 'reward_earned']

class TaskSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskSubmission
        fields = '__all__'
        read_only_fields = ['assignment', 'submitted_at', 'reviewed_at', 'is_approved', 'reviewer_notes']

class TaskListSerializer(serializers.ModelSerializer):
    available_spots = serializers.SerializerMethodField()
    plan_required_name = serializers.CharField(source='plan_required.name', read_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'reward', 'max_assignments', 'current_assignments', 
                 'available_spots', 'deadline', 'status', 'is_simulated', 'plan_required_name']
    
    def get_available_spots(self, obj):
        return obj.max_assignments - obj.current_assignments

class TaskActivityLogSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = TaskActivityLog
        fields = '__all__'
        read_only_fields = ['timestamp']