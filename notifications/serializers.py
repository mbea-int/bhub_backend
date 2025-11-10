from rest_framework import serializers
from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'message', 'related_type', 'related_id',
            'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']