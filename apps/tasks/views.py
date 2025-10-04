from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, F
from django.core.paginator import Paginator
from .models import Task, TaskAssignment, TaskSubmission, TaskActivityLog
from .serializers import TaskSerializer, TaskAssignmentSerializer, TaskSubmissionSerializer, TaskListSerializer, TaskActivityLogSerializer
from apps.plans.models import Plan
from apps.users.models import User
from apps.wallets.models import Wallet, Transaction
from apps.notifications.models import Notification
from apps.notifications.utils import send_notification
from apps.core.utils import validate_kyc_document
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_detail_api(request, task_id):
    """API endpoint for getting a specific task's details"""
    if request.user.user_type not in ['admin', 'moderator']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    try:
        task = Task.objects.get(id=task_id)
        serializer = TaskSerializer(task)
        return Response(serializer.data)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_list_view(request):
    """Get available tasks for freelancers"""
    if request.user.active_role not in ['freelancer', 'both']:
        return Response({'error': 'Access denied - freelancer role required'}, status=status.HTTP_403_FORBIDDEN)

    if not request.user.can_access_freelancer_features():
        return Response({'error': 'No active freelancer subscription'}, status=status.HTTP_400_BAD_REQUEST)

    # Get current plan
    current_plan = Plan.objects.get(name=request.user.current_freelancer_plan)

    # Get tasks that are available and match the user's plan requirements
    tasks = Task.objects.filter(
        Q(plan_required__priority__lte=current_plan.priority) | Q(is_simulated=True),
        status__in=['active', 'simulated'],
        deadline__gt=timezone.now(),
        current_assignments__lt=F('max_assignments')
    ).select_related('plan_required').order_by('-created_at')

    serializer = TaskListSerializer(tasks, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_task_view(request, task_id):
    """Assign a task to freelancer"""
    if request.user.active_role not in ['freelancer', 'both']:
        return Response({'error': 'Access denied - freelancer role required'}, status=status.HTTP_403_FORBIDDEN)

    try:
        task = Task.objects.get(id=task_id)

        if not task.is_available:
            return Response({'error': 'Task is not available'}, status=status.HTTP_400_BAD_REQUEST)

        # Check plan requirements (skip for simulated tasks)
        if not task.is_simulated:
            current_plan = Plan.objects.get(name=request.user.current_freelancer_plan)
            if task.plan_required and task.plan_required.priority > current_plan.priority:
                return Response({'error': 'Your plan does not have access to this task'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user has reached assignment limit
        active_assignments = TaskAssignment.objects.filter(
            user=request.user,
            status__in=['accepted', 'submitted']
        ).count()

        if active_assignments >= current_plan.max_concurrent_tasks:
            return Response({'error': 'You have reached your concurrent task limit'}, status=status.HTTP_400_BAD_REQUEST)

        assignment, created = TaskAssignment.objects.get_or_create(
            task=task,
            user=request.user,
            defaults={'status': 'accepted'}
        )

        if created:
            task.current_assignments += 1
            task.save()

            # Log activity
            TaskActivityLog.objects.create(
                task=task,
                user=request.user,
                activity_type='assigned',
                details={'freelancer_id': request.user.id}
            )
        elif assignment.status != 'pending':
            return Response({'error': 'Task already assigned'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            assignment.status = 'accepted'
            assignment.save()

            # Log activity
            TaskActivityLog.objects.create(
                task=task,
                user=request.user,
                activity_type='accepted',
                details={'freelancer_id': request.user.id}
            )

        return Response({'message': 'Task assigned successfully', 'assignment_id': assignment.id})

    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_task_view(request, assignment_id):
    """Submit completed task"""
    if request.user.active_role not in ['freelancer', 'both']:
        return Response({'error': 'Access denied - freelancer role required'}, status=status.HTTP_403_FORBIDDEN)

    try:
        assignment = TaskAssignment.objects.get(id=assignment_id, user=request.user)

        if assignment.status != 'accepted':
            return Response({'error': 'Task not accepted'}, status=status.HTTP_400_BAD_REQUEST)

        submission = TaskSubmission.objects.create(
            assignment=assignment,
            files=request.data.get('files', []),
            notes=request.data.get('notes', '')
        )

        assignment.status = 'submitted'
        assignment.submitted_at = timezone.now()
        assignment.save()

        # Log activity
        TaskActivityLog.objects.create(
            task=assignment.task,
            user=request.user,
            activity_type='submitted',
            details={'freelancer_id': request.user.id, 'submission_id': submission.id}
        )

        # Notify admin
        send_notification(
            user_type='admin',
            title='New Task Submission',
            message=f'Freelancer {request.user.username} has submitted task {assignment.task.title}',
            notification_type='task_submission'
        )

        # Notify client (if applicable)
        if assignment.task.created_by.user_type == 'client':
            send_notification(
                user=assignment.task.created_by,
                title='Task Submitted',
                message=f'Your task "{assignment.task.title}" has been submitted by {request.user.username}',
                notification_type='task_submitted'
            )

        return Response({'message': 'Task submitted successfully', 'submission_id': submission.id})

    except TaskAssignment.DoesNotExist:
        return Response({'error': 'Assignment not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_assignments_view(request):
    """Get user's task assignments"""
    assignments = TaskAssignment.objects.filter(user=request.user).select_related('task')
    serializer = TaskAssignmentSerializer(assignments, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_review_submission(request, submission_id):
    """Admin review of task submission"""
    if request.user.user_type not in ['admin', 'moderator']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    try:
        submission = TaskSubmission.objects.get(id=submission_id)
        is_approved = request.data.get('is_approved', False)
        reviewer_notes = request.data.get('reviewer_notes', '')

        submission.is_approved = is_approved
        submission.reviewer_notes = reviewer_notes
        submission.reviewed_at = timezone.now()
        submission.save()

        assignment = submission.assignment
        assignment.status = 'approved' if is_approved else 'rejected'
        assignment.reviewed_at = timezone.now()

        if is_approved:
            # Apply plan multiplier
            plan = Plan.objects.get(name=assignment.user.current_freelancer_plan)
            reward_with_multiplier = assignment.task.reward * plan.task_reward_multiplier

            assignment.reward_earned = reward_with_multiplier
            assignment.user.total_earnings += reward_with_multiplier
            assignment.user.save()

            # Add to wallet
            wallet, created = Wallet.objects.get_or_create(user=assignment.user)
            Transaction.objects.create(
                wallet=wallet,
                amount=reward_with_multiplier,
                transaction_type='earning',
                description=f'Task completion: {assignment.task.title}',
                reference=f'task_{assignment.task.id}'
            )

            # Notify freelancer
            send_notification(
                user=assignment.user,
                title='Task Approved',
                message=f'Your submission for task "{assignment.task.title}" has been approved. ${reward_with_multiplier} earned.',
                notification_type='task_approval'
            )

            # Notify client
            send_notification(
                user=assignment.task.created_by,
                title='Task Completed',
                message=f'Task "{assignment.task.title}" has been completed successfully',
                notification_type='task_completed'
            )
        else:
            send_notification(
                user=assignment.user,
                title='Task Rejected',
                message=f'Your submission for task "{assignment.task.title}" has been rejected. Reason: {reviewer_notes}',
                notification_type='task_rejection'
            )

        assignment.save()

        # Log activity
        TaskActivityLog.objects.create(
            task=assignment.task,
            user=request.user,
            activity_type='approved' if is_approved else 'rejected',
            details={'admin_id': request.user.id, 'reviewer_notes': reviewer_notes}
        )

        return Response({'message': 'Submission reviewed successfully'})

    except TaskSubmission.DoesNotExist:
        return Response({'error': 'Submission not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_simulated_task_view(request):
    """Admin create simulated task for freelancer feed"""
    if request.user.user_type not in ['admin', 'moderator']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    title = request.data.get('title')
    description = request.data.get('description')
    reward = request.data.get('reward')
    plan_required_id = request.data.get('plan_required_id')

    if not all([title, description, reward]):
        return Response({'error': 'Title, description, and reward are required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        plan = Plan.objects.get(id=plan_required_id) if plan_required_id else None
    except Plan.DoesNotExist:
        return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_REQUEST)

    task = Task.objects.create(
        title=title,
        description=description,
        reward=reward,
        max_assignments=100,  # Simulated tasks can have many assignments
        plan_required=plan,
        status='simulated',
        created_by=request.user,
        is_simulated=True
    )

    # Log activity
    TaskActivityLog.objects.create(
        task=task,
        user=request.user,
        activity_type='created',
        details={'admin_id': request.user.id, 'is_simulated': True}
    )

    return Response({
        'message': 'Simulated task created successfully',
        'task_id': task.id
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_activity_logs_view(request, task_id):
    """Get activity logs for a task"""
    if request.user.user_type not in ['admin', 'moderator']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    try:
        task = Task.objects.get(id=task_id)
        logs = TaskActivityLog.objects.filter(task=task).order_by('-timestamp')
        serializer = TaskActivityLogSerializer(logs, many=True)
        return Response(serializer.data)
    except Task.DoesNotExist:
        return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)