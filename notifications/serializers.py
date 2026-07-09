from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'body', 'is_read', 'request', 'created_at']
        read_only_fields = ['id', 'title', 'body', 'request', 'created_at']
