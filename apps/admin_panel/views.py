from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from apps.users.models import User, LoginAttempt
from apps.tasks.models import Task, TaskAssignment, TaskSubmission
from apps.plans.models import Plan
from apps.payments.models import Deposit, Withdrawal
from apps.notifications.models import Notification, Message
from apps.wallets.models import Wallet, Transaction
from apps.referrals.models import ReferralBonus
from django.db.models import Count, Sum, Avg
from datetime import datetime, timedelta
from collections import defaultdict
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_dashboard_view(request):
    if request.user.user_type not in ['admin', 'moderator']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    # User statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    verified_users = User.objects.filter(is_email_verified=True, is_phone_verified=True).count()
    
    # Task statistics
    total_tasks = Task.objects.count()
    active_tasks = Task.objects.filter(status='active').count()
    completed_tasks = Task.objects.filter(status='completed').count()
    
    # Payment statistics
    total_deposits = Deposit.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
    total_withdrawals = Withdrawal.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
    pending_withdrawals = Withdrawal.objects.filter(status='pending').count()
    
    # Revenue statistics
    total_earnings = User.objects.aggregate(total=Sum('total_earnings'))['total'] or 0
    
    dashboard_data = {
        'users': {
            'total': total_users,
            'active': active_users,
            'verified': verified_users,
        },
        'tasks': {
            'total': total_tasks,
            'active': active_tasks,
            'completed': completed_tasks,
        },
        'payments': {
            'total_deposits': float(total_deposits),
            'total_withdrawals': float(total_withdrawals),
            'pending_withdrawals': pending_withdrawals,
        },
        'revenue': {
            'total_earnings': float(total_earnings),
        }
    }
    
    return Response(dashboard_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_management_view(request):
    if request.user.user_type not in ['admin', 'moderator']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    users = User.objects.all().select_related('wallet').order_by('-created_at')
    
    user_data = []
    for user in users:
        wallet, created = Wallet.objects.get_or_create(user=user)
        user_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'phone_number': str(user.phone_number),
            'plan': user.plan,
            'is_active': user.is_active,
            'is_email_verified': user.is_email_verified,
            'is_phone_verified': user.is_phone_verified,
            'is_kyc_verified': user.is_kyc_verified,
            'total_earnings': float(user.total_earnings),
            'wallet_balance': float(wallet.balance),
            'created_at': user.created_at,
        })
    
    return Response(user_data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_user_status_view(request, user_id):
    if request.user.user_type not in ['admin', 'moderator']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        user = User.objects.get(id=user_id)
        action = request.data.get('action')
        
        if action == 'activate':
            user.is_active = True
            user.save()
        elif action == 'deactivate':
            user.is_active = False
            user.save()
        elif action == 'verify_email':
            user.is_email_verified = True
            user.save()
        elif action == 'verify_phone':
            user.is_phone_verified = True
            user.save()
        elif action == 'verify_kyc':
            user.is_kyc_verified = True
            user.save()
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'message': 'User status updated successfully'})
    
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_management_view(request):
    if request.user.user_type not in ['admin', 'moderator']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    tasks = Task.objects.all().select_related('created_by', 'plan_required').order_by('-created_at')
    
    task_data = []
    for task in tasks:
        task_data.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'reward': float(task.reward),
            'max_assignments': task.max_assignments,
            'current_assignments': task.current_assignments,
            'plan_required': task.plan_required.name,
            'status': task.status,
            'created_by': task.created_by.username,
            'created_at': task.created_at,
            'deadline': task.deadline,
        })
    
    return Response(task_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_overview_view(request):
    if request.user.user_type not in ['admin', 'moderator']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    # Get transaction statistics
    deposits = Deposit.objects.filter(status='completed')
    withdrawals = Withdrawal.objects.filter(status='completed')
    earnings = Transaction.objects.filter(transaction_type='earning')
    
    deposit_stats = deposits.aggregate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    withdrawal_stats = withdrawals.aggregate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    earning_stats = earnings.aggregate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    return Response({
        'deposits': {
            'total': float(deposit_stats['total'] or 0),
            'count': deposit_stats['count'] or 0,
        },
        'withdrawals': {
            'total': float(withdrawal_stats['total'] or 0),
            'count': withdrawal_stats['count'] or 0,
        },
        'earnings': {
            'total': float(earning_stats['total'] or 0),
            'count': earning_stats['count'] or 0,
        }
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def fraud_detection_view(request):
    if request.user.user_type not in ['admin', 'moderator']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    # Find potential duplicate accounts
    duplicate_emails = User.objects.values('email').annotate(count=Count('id')).filter(count__gt=1)
    duplicate_phones = User.objects.exclude(phone_number__isnull=True).values('phone_number').annotate(count=Count('id')).filter(count__gt=1)
    
    # Find suspicious login attempts
    recent_attempts = LoginAttempt.objects.filter(
        timestamp__gte=datetime.now() - timedelta(hours=24)
    ).values('ip_address').annotate(count=Count('id')).filter(count__gt=5)
    
    fraud_data = {
        'duplicate_emails': list(duplicate_emails),
        'duplicate_phones': list(duplicate_phones),
        'suspicious_ips': list(recent_attempts),
    }
    
    return Response(fraud_data)