from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Document, DocumentUpload
from .serializers import DocumentSerializer, DocumentUploadSerializer
from apps.users.models import User
from apps.tasks.models import Task
from apps.notifications.utils import send_notification
import os
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_document_view(request):
    """Upload document for task submission (client role)"""
    if request.user.active_role not in ['client', 'both']:
        return Response({'error': 'Access denied - client role required'}, status=status.HTTP_403_FORBIDDEN)
    
    if not request.user.can_access_client_features():
        return Response({'error': 'No active client subscription'}, status=status.HTTP_400_BAD_REQUEST)
    
    file = request.FILES.get('file')
    description = request.data.get('description', '')
    
    if not file:
        return Response({'error': 'File is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate file type and size
    allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png', '.gif', '.bmp']
    file_extension = file.name.split('.')[-1].lower()
    if f'.{file_extension}' not in allowed_extensions:
        return Response({'error': 'Invalid file type'}, status=status.HTTP_400_BAD_REQUEST)
    
    if file.size > 10 * 1024 * 1024:  # 10MB limit
        return Response({'error': 'File too large (max 10MB)'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Determine file type
    if file_extension in ['pdf']:
        file_type = 'pdf'
    elif file_extension in ['doc', 'docx']:
        file_type = 'word'
    elif file_extension in ['xls', 'xlsx']:
        file_type = 'excel'
    elif file_extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
        file_type = 'image'
    else:
        file_type = 'text'
    
    document = Document.objects.create(
        user=request.user,
        file=file,
        filename=file.name,
        file_type=file_type,
        file_size=file.size,
        description=description,
        status='uploaded'
    )
    
    # Process document (in real app, this might involve OCR, validation, etc.)
    document.status = 'ready'
    document.processed_at = timezone.now()
    document.save()
    
    return Response({
        'message': 'Document uploaded successfully',
        'document_id': document.id,
        'file_size_mb': document.file_size_mb
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_documents_view(request):
    """Get documents uploaded by client"""
    if request.user.active_role not in ['client', 'both']:
        return Response({'error': 'Access denied - client role required'}, status=status.HTTP_403_FORBIDDEN)
    
    documents = Document.objects.filter(user=request.user).order_by('-uploaded_at')
    serializer = DocumentSerializer(documents, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_task_from_document_view(request):
    """Create a task from an uploaded document (client role)"""
    if request.user.active_role not in ['client', 'both']:
        return Response({'error': 'Access denied - client role required'}, status=status.HTTP_403_FORBIDDEN)
    
    if not request.user.can_access_client_features():
        return Response({'error': 'No active client subscription'}, status=status.HTTP_400_BAD_REQUEST)
    
    serializer = DocumentUploadSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        upload = serializer.save()
        
        # Create task from document
        task = Task.objects.create(
            title=upload.task_title,
            description=upload.task_description,
            reward=0,  # Will be set by admin or based on complexity
            max_assignments=1,
            plan_required=None,  # Will be set by admin
            status='pending',
            created_by=request.user
        )
        
        # Link document to task
        upload.document.task = task
        upload.document.save()
        
        # Notify admin
        send_notification(
            user_type='admin',
            title='New Task Submitted',
            message=f'Client {request.user.username} has submitted a new task with document',
            notification_type='task_submission'
        )
        
        return Response({
            'message': 'Task created successfully',
            'task_id': task.id,
            'upload_id': upload.id
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)