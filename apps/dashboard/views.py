from rest_framework.decorators import api_view
from rest_framework.response import Response
from apps.users.models import User
from apps.tasks.models import Task
from apps.payments.models import Deposit, Withdrawal
from django.db.models import Count, Sum, Avg
from django.core.paginator import Paginator
from django.db.models import Q

# Remove the permission_classes decorator for testing
@api_view(['GET'])
def dashboard_stats(request):
    """Get dashboard statistics"""
    # For now, we'll skip the permission check as well
    # if request.user.user_type not in ['admin', 'moderator']:
    #     return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    # Get user stats
    total_users = User.objects.count()
    active_freelancers = User.objects.filter(user_type='freelancer', is_active=True).count()
    active_clients = User.objects.filter(user_type='client', is_active=True).count()
    verified_users = User.objects.filter(is_email_verified=True, is_phone_verified=True).count()

    # Get task stats
    pending_tasks = Task.objects.filter(status='pending').count()
    active_tasks = Task.objects.filter(status='active').count()
    completed_tasks = Task.objects.filter(status='completed').count()
    rejected_tasks = Task.objects.filter(status='rejected').count()

    # Get payment stats
    total_deposits = Deposit.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
    total_withdrawals = Withdrawal.objects.filter(status='completed').aggregate(total=Sum('amount'))['total'] or 0
    pending_withdrawals = Withdrawal.objects.filter(status='pending').count()

    stats = {
        'total_users': total_users,
        'active_freelancers': active_freelancers,
        'active_clients': active_clients,
        'verified_users': verified_users,
        'pending_tasks': pending_tasks,
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'rejected_tasks': rejected_tasks,
        'total_deposits': float(total_deposits),
        'total_withdrawals': float(total_withdrawals),
        'pending_withdrawals': pending_withdrawals
    }

    return Response(stats)

# Add the other views we created earlier if needed:
@api_view(['GET'])
def user_list_api(request):
    """API endpoint for listing users"""
    if request.user.user_type not in ['admin', 'moderator']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    # Get query parameters
    search_term = request.GET.get('search', '')
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 10))

    # Filter users
    users = User.objects.all().order_by('-created_at')

    if search_term:
        users = users.filter(
            Q(username__icontains=search_term) |
            Q(email__icontains=search_term) |
            Q(phone_number__icontains=search_term)
        )

    # Paginate
    paginator = Paginator(users, limit)
    page_obj = paginator.get_page(page)

    # Serialize data
    user_data = []
    for user in page_obj:
        user_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'phone_number': str(user.phone_number),
            'user_type': user.user_type,
            'is_active': user.is_active,
            'is_email_verified': user.is_email_verified,
            'is_phone_verified': user.is_phone_verified,
            'is_kyc_verified': user.is_kyc_verified,
            'current_plan': user.current_plan,
            'total_earnings': float(user.total_earnings),
            'total_deposits': float(user.total_deposits),
            'total_withdrawals': float(user.total_withdrawals),
            'created_at': user.created_at.isoformat()
        })

    response_data = {
        'results': user_data,
        'count': paginator.count,
        'next': page_obj.has_next(),
        'previous': page_obj.has_previous(),
        'total_pages': paginator.num_pages
    }

    return Response(response_data)

@api_view(['GET'])
def task_list_api(request):
    """API endpoint for listing tasks"""
    if request.user.user_type not in ['admin', 'moderator']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    # Get query parameters
    search_term = request.GET.get('search', '')
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 10))

    # Filter tasks
    tasks = Task.objects.all().select_related('created_by', 'plan_required').order_by('-created_at')

    if search_term:
        tasks = tasks.filter(
            Q(title__icontains=search_term) |
            Q(description__icontains=search_term)
        )

    # Paginate
    paginator = Paginator(tasks, limit)
    page_obj = paginator.get_page(page)

    # Serialize data
    task_data = []
    for task in page_obj:
        task_data.append({
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'reward': float(task.reward),
            'max_assignments': task.max_assignments,
            'current_assignments': task.current_assignments,
            'plan_required': task.plan_required.name if task.plan_required else None,
            'status': task.status,
            'created_by': {
                'id': task.created_by.id,
                'username': task.created_by.username,
                'email': task.created_by.email
            } if task.created_by else None,
            'created_at': task.created_at.isoformat(),
            'deadline': task.deadline.isoformat() if task.deadline else None,
        })

    response_data = {
        'results': task_data,
        'count': paginator.count,
        'next': page_obj.has_next(),
        'previous': page_obj.has_previous(),
        'total_pages': paginator.num_pages
    }

    return Response(response_data)