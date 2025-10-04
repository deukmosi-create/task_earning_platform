from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import models
from .models import Notification, Message
from .serializers import NotificationSerializer, MessageSerializer, CreateMessageSerializer
from apps.users.models import User
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user)
    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_notification_read_view(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return Response({'message': 'Notification marked as read'})
    except Notification.DoesNotExist:
        return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unread_notifications_count_view(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({'count': count})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def messages_view(request):
    messages = Message.objects.filter(
        models.Q(sender=request.user) | models.Q(receiver=request.user)
    ).select_related('sender', 'receiver')
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message_view(request):
    serializer = CreateMessageSerializer(data=request.data)
    if serializer.is_valid():
        try:
            receiver = User.objects.get(
                id=serializer.validated_data['receiver_id'],
                user_type__in=['admin', 'moderator']
            )
            
            message = Message.objects.create(
                sender=request.user,
                receiver=receiver,
                subject=serializer.validated_data['subject'],
                message=serializer.validated_data['message'],
                message_type='user_to_admin'
            )
            
            # Create notification for admin
            Notification.objects.create(
                user=receiver,
                title=f'New message from {request.user.username}',
                message=serializer.validated_data['message'][:100],
                notification_type='message_received',
                data={'sender_id': request.user.id, 'message_id': message.id}
            )
            
            return Response({'message': 'Message sent successfully', 'message_id': message.id})
        
        except User.DoesNotExist:
            return Response({'error': 'Admin user not found'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reply_message_view(request, message_id):
    try:
        original_message = Message.objects.get(id=message_id)
        
        if request.user.user_type not in ['admin', 'moderator']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        reply_message = Message.objects.create(
            sender=request.user,
            receiver=original_message.sender,
            subject=f'Re: {original_message.subject}',
            message=request.data.get('message', ''),
            message_type='admin_to_user',
            replied_to=original_message
        )
        
        # Create notification for user
        Notification.objects.create(
            user=original_message.sender,
            title=f'Reply from {request.user.username}',
            message=request.data.get('message', '')[:100],
            notification_type='message_received',
            data={'sender_id': request.user.id, 'message_id': reply_message.id}
        )
        
        return Response({'message': 'Reply sent successfully', 'message_id': reply_message.id})
    
    except Message.DoesNotExist:
        return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)