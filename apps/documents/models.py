from django.db import models
from apps.users.models import User
from apps.tasks.models import Task

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('pdf', 'PDF'),
        ('word', 'Word Document'),
        ('excel', 'Excel Spreadsheet'),
        ('image', 'Image'),
        ('text', 'Text File'),
    ]
    
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    file = models.FileField(upload_to='task_documents/')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file_size = models.PositiveIntegerField()  # in bytes
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.filename} - {self.user.username}"
    
    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2)

class DocumentUpload(models.Model):
    """Track document uploads for clients"""
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_uploads')
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    task_title = models.CharField(max_length=200)
    task_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.client.username} - {self.task_title}"