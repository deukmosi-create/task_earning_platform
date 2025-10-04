from django.db import models
from apps.users.models import User

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('task_assignment', 'Task Assignment'),
        ('task_submission', 'Task Submission'),
        ('task_approval', 'Task Approval'),
        ('task_rejection', 'Task Rejection'),
        ('deposit_completed', 'Deposit Completed'),
        ('withdrawal_completed', 'Withdrawal Completed'),
        ('plan_upgrade', 'Plan Upgrade'),
        ('system_message', 'System Message'),
        ('message_received', 'Message Received'),
        ('account_activated', 'Account Activated'),
        ('task_completed', 'Task Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    user_type = models.CharField(max_length=20, null=True, blank=True)
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username if self.user else 'Admin'}"

class Message(models.Model):
    MESSAGE_TYPES = [
        ('user_to_admin', 'User to Admin'),
        ('admin_to_user', 'Admin to User'),
        ('moderator_to_user', 'Moderator to User'),
    ]
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=200)
    message = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    is_read = models.BooleanField(default=False)
    replied_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.username} to {self.receiver.username}"