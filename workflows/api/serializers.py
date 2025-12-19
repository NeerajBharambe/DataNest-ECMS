from rest_framework import serializers
from workflows.models import Task

class TaskSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(
        source='document.title',
        read_only=True
    )

    class Meta:
        model = Task
        fields = [
            'id',
            'document',
            'document_title',
            'status',
            'comments',
            'created_at'
        ]
        read_only_fields = ['document', 'created_at']