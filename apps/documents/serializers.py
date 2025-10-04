from rest_framework import serializers
from .models import Document, DocumentUpload
from apps.tasks.models import Task

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['user', 'file_size', 'status', 'uploaded_at', 'processed_at']

class DocumentUploadSerializer(serializers.ModelSerializer):
    document_id = serializers.IntegerField(write_only=True)
    task_title = serializers.CharField()
    task_description = serializers.CharField()
    
    class Meta:
        model = DocumentUpload
        fields = ['document_id', 'task_title', 'task_description']
    
    def validate_document_id(self, value):
        try:
            document = Document.objects.get(id=value, user=self.context['request'].user)
            if document.status != 'ready':
                raise serializers.ValidationError("Document is not ready for upload")
            return document
        except Document.DoesNotExist:
            raise serializers.ValidationError("Document not found")
    
    def create(self, validated_data):
        document = validated_data.pop('document_id')
        upload = DocumentUpload.objects.create(
            client=self.context['request'].user,
            document=document,
            **validated_data
        )
        
        # Update document status
        document.status = 'ready'
        document.save()
        
        return upload