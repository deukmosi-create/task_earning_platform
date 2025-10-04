# Create an empty file: apps/plans/models.py (for now, we'll add content later)
from django.db import models

class Plan(models.Model):
    PLAN_CHOICES = [
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
    ]
    
    name = models.CharField(max_length=20, choices=PLAN_CHOICES, unique=True)
    priority = models.IntegerField(default=1)
    daily_task_limit = models.IntegerField(default=5)
    max_concurrent_tasks = models.IntegerField(default=3)
    task_reward_multiplier = models.DecimalField(max_digits=3, decimal_places=2, default=1.00)
    monthly_price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    features = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class PlanUpgrade(models.Model):
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    old_plan = models.CharField(max_length=20)
    new_plan = models.CharField(max_length=20)
    upgrade_cost = models.DecimalField(max_digits=8, decimal_places=2)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='completed')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.old_plan} to {self.new_plan}"