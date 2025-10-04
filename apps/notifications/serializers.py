from rest_framework import serializers
from .models import Notification, Message

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)
    
    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ['sender', 'created_at', 'updated_at']

class CreateMessageSerializer(serializers.Serializer):
    receiver_id = serializers.IntegerField()
    subject = serializers.CharField()
    message = serializers.CharField()