from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.users.models import User
from apps.tasks.models import Task
from apps.documents.models import Document, DocumentUpload
from apps.payments.models import Deposit
from apps.wallets.models import Wallet
from apps.notifications.utils import send_notification
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_dashboard_view(request):
    """Client dashboard with stats and activity"""
    if request.user.active_role not in ['client', 'both']:
        return Response({'error': 'Access denied - client role required'}, status=status.HTTP_403_FORBIDDEN)
    
    if not request.user.can_access_client_features():
        return Response({'error': 'No active client subscription'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Get client stats
    total_deposits = request.user.total_deposits
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    balance = wallet.balance
    
    # Tasks created by client
    created_tasks = Task.objects.filter(created_by=request.user).count()
    
    # Active tasks
    active_tasks = Task.objects.filter(
        created_by=request.user,
        status__in=['pending', 'active']
    ).count()
    
    # Completed tasks
    completed_tasks = Task.objects.filter(
        created_by=request.user,
        status='completed'
    ).count()
    
    # Recent document uploads
    recent_uploads = DocumentUpload.objects.filter(
        client=request.user
    ).select_related('document').order_by('-created_at')[:5]
    
    dashboard_data = {
        'stats': {
            'total_deposits': float(total_deposits),
            'balance': float(balance),
            'created_tasks': created_tasks,
            'active_tasks': active_tasks,
            'completed_tasks': completed_tasks,
        },
        'recent_uploads': [
            {
                'task_title': upload.task_title,
                'filename': upload.document.filename,
                'file_size_mb': upload.document.file_size_mb,
                'uploaded_at': upload.created_at,
                'status': upload.document.status,
            }
            for upload in recent_uploads
        ],
        'current_plan': request.user.current_client_plan,
    }
    
    return Response(dashboard_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_tasks_view(request):
    """Get tasks created by client"""
    if request.user.active_role not in ['client', 'both']:
        return Response({'error': 'Access denied - client role required'}, status=status.HTTP_403_FORBIDDEN)
    
    tasks = Task.objects.filter(created_by=request.user).order_by('-created_at')
    
    tasks_data = [
        {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'reward': float(task.reward),
            'status': task.status,
            'created_at': task.created_at,
            'deadline': task.deadline,
            'current_assignments': task.current_assignments,
            'max_assignments': task.max_assignments,
        }
        for task in tasks
    ]
    
    return Response(tasks_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_documents_view(request):
    """Get documents uploaded by client"""
    if request.user.active_role not in ['client', 'both']:
        return Response({'error': 'Access denied - client role required'}, status=status.HTTP_403_FORBIDDEN)
    
    documents = Document.objects.filter(user=request.user).order_by('-uploaded_at')
    
    documents_data = [
        {
            'id': doc.id,
            'filename': doc.filename,
            'file_type': doc.file_type,
            'file_size_mb': doc.file_size_mb,
            'description': doc.description,
            'status': doc.status,
            'uploaded_at': doc.uploaded_at,
        }
        for doc in documents
    ]
    
    return Response(documents_data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def activate_client_account_view(request):
    """Activate client account with deposit"""
    if request.user.active_role not in ['client', 'both']:
        return Response({'error': 'Access denied - client role required'}, status=status.HTTP_403_FORBIDDEN)
    
    amount = request.data.get('amount')
    
    if not amount or float(amount) <= 0:
        return Response({'error': 'Valid amount is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check if user has sufficient balance
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    if wallet.balance < float(amount):
        return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Process activation
    request.user.is_account_activated = True
    request.user.save()
    
    # Record deposit
    Deposit.objects.create(
        user=request.user,
        amount=amount,
        payment_method='account_activation',
        transaction_id=f'activation_{request.user.id}',
        status='completed'
    )
    
    # Update user totals
    request.user.total_deposits += float(amount)
    request.user.save()
    
    # Update wallet
    Transaction.objects.create(
        wallet=wallet,
        amount=float(amount),
        transaction_type='deposit',
        description='Account activation deposit',
        reference=f'activation_{request.user.id}'
    )
    
    # Send notification
    send_notification(
        user=request.user,
        title='Account Activated',
        message='Your client account has been activated successfully',
        notification_type='account_activated'
    )
    
    return Response({'message': 'Account activated successfully'})