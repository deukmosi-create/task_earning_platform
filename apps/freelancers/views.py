from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.users.models import User
from apps.tasks.models import TaskAssignment, TaskSubmission
from apps.plans.models import Plan
from apps.wallets.models import Wallet, Transaction
from apps.notifications.models import Notification
from apps.notifications.utils import send_notification
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def freelancer_dashboard_view(request):
    """Freelancer dashboard with stats and activity"""
    if request.user.active_role not in ['freelancer', 'both']:
        return Response({'error': 'Access denied - freelancer role required'}, status=status.HTTP_403_FORBIDDEN)
    
    # Get freelancer stats
    total_earnings = request.user.total_earnings
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    balance = wallet.balance
    
    # Active assignments
    active_assignments = TaskAssignment.objects.filter(
        user=request.user,
        status__in=['accepted', 'submitted']
    ).count()
    
    # Completed assignments
    completed_assignments = TaskAssignment.objects.filter(
        user=request.user,
        status='approved'
    ).count()
    
    # Recent submissions
    recent_submissions = TaskSubmission.objects.filter(
        assignment__user=request.user
    ).select_related('assignment__task').order_by('-submitted_at')[:5]
    
    dashboard_data = {
        'stats': {
            'total_earnings': float(total_earnings),
            'balance': float(balance),
            'active_assignments': active_assignments,
            'completed_assignments': completed_assignments,
        },
        'recent_submissions': [
            {
                'task_title': submission.assignment.task.title,
                'status': submission.assignment.status,
                'submitted_at': submission.submitted_at,
                'reward_earned': float(submission.assignment.reward_earned),
            }
            for submission in recent_submissions
        ],
        'current_plan': request.user.current_freelancer_plan,
    }
    
    return Response(dashboard_data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def freelancer_earnings_view(request):
    """Get freelancer earnings history"""
    if request.user.active_role not in ['freelancer', 'both']:
        return Response({'error': 'Access denied - freelancer role required'}, status=status.HTTP_403_FORBIDDEN)
    
    transactions = Transaction.objects.filter(
        wallet__user=request.user,
        transaction_type='earning'
    ).order_by('-created_at')
    
    earnings_data = [
        {
            'amount': float(t.amount),
            'description': t.description,
            'date': t.created_at,
            'reference': t.reference
        }
        for t in transactions
    ]
    
    return Response({
        'total_earnings': float(request.user.total_earnings),
        'earnings_history': earnings_data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def freelancer_profile_view(request):
    """Get freelancer profile information"""
    if request.user.active_role not in ['freelancer', 'both']:
        return Response({'error': 'Access denied - freelancer role required'}, status=status.HTTP_403_FORBIDDEN)
    
    # Get plan details
    plan = Plan.objects.get(name=request.user.current_freelancer_plan)
    
    profile_data = {
        'username': request.user.username,
        'email': request.user.email,
        'phone_number': str(request.user.phone_number),
        'current_plan': plan.name,
        'plan_features': plan.features,
        'daily_task_limit': plan.daily_task_limit,
        'max_concurrent_tasks': plan.max_concurrent_tasks,
        'task_reward_multiplier': float(plan.task_reward_multiplier),
        'is_kyc_verified': request.user.is_kyc_verified,
        'is_account_activated': request.user.is_account_activated,
        'total_earnings': float(request.user.total_earnings),
    }
    
    return Response(profile_data)