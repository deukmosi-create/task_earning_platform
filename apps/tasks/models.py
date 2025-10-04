from django.db import models
from apps.users.models import User
from apps.plans.models import Plan
from django.utils import timezone

class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('simulated', 'Simulated'),  # Admin-created tasks
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    reward = models.DecimalField(max_digits=10, decimal_places=2)
    max_assignments = models.IntegerField(default=1)
    current_assignments = models.IntegerField(default=0)
    plan_required = models.ForeignKey(Plan, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deadline = models.DateTimeField(null=True, blank=True)
    is_simulated = models.BooleanField(default=False)  # True for admin-created tasks
    
    def __str__(self):
        return self.title
    
    @property
    def is_available(self):
        return (self.status in ['active', 'simulated'] and 
                self.current_assignments < self.max_assignments and
                (not self.deadline or self.deadline > timezone.now()))

class TaskAssignment(models.Model):
    assignment_status = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_assignments')
    status = models.CharField(max_length=20, choices=assignment_status, default='pending')
    assigned_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    submission_notes = models.TextField(blank=True)
    reviewer_notes = models.TextField(blank=True)
    reward_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    class Meta:
        unique_together = ['task', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.task.title}"

class TaskSubmission(models.Model):
    assignment = models.OneToOneField(TaskAssignment, on_delete=models.CASCADE, related_name='submission')
    files = models.JSONField(default=list)  # Store file paths/URLs
    notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    is_approved = models.BooleanField(default=False)
    reviewer_notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Submission for {self.assignment.task.title}"

class TaskActivityLog(models.Model):
    ACTIVITY_TYPES = [
        ('created', 'Task Created'),
        ('assigned', 'Task Assigned'),
        ('accepted', 'Task Accepted'),
        ('submitted', 'Task Submitted'),
        ('approved', 'Task Approved'),
        ('rejected', 'Task Rejected'),
        ('cancelled', 'Task Cancelled'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='activity_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.activity_type} - {self.task.title}"