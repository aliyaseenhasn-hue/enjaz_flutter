from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

from .models import (
    Category, RequestAttachment, RequestMessage,
    RequestTimeline, Review, ServiceRequest, WalletTransaction,
)

class CategorySerializer(serializers.ModelSerializer):
    name_ar = serializers.CharField(source='name', read_only=True)
    class Meta:
        model = Category
        fields = ['id', 'name', 'name_ar', 'icon', 'description', 'is_active']

class SimpleUserSerializer(serializers.ModelSerializer):
    profile_photo = serializers.SerializerMethodField()
    class Meta:
        model = User
        fields = ['id', 'full_name', 'profile_photo']

    def get_profile_photo(self, obj):
        if obj.avatar:
            return f"https://njazzz.pythonanywhere.com{obj.avatar.url}"
        return None

class RequestAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestAttachment
        fields = ['id', 'file', 'uploaded_at']

class RequestTimelineSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestTimeline
        fields = ['id', 'status', 'comment', 'timestamp']

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'rating', 'comment', 'created_at']

class ServiceRequestListSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    customer_name = serializers.SerializerMethodField()

    def get_category_name(self, obj):
        return obj.category.name if obj.category else ""

    def get_customer_name(self, obj):
        return obj.customer.full_name if obj.customer else ""

    class Meta:
        model = ServiceRequest
        fields = ['id', 'title', 'category_name', 'customer_name', 'status', 'status_display', 'created_at']

class ServiceRequestDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    customer = SimpleUserSerializer(read_only=True, allow_null=True)
    agent = SimpleUserSerializer(read_only=True, allow_null=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    attachments = RequestAttachmentSerializer(many=True, read_only=True)
    timeline = RequestTimelineSerializer(many=True, read_only=True)
    review = ReviewSerializer(read_only=True)
    class Meta:
        model = ServiceRequest
        fields = [
            'id', 'title', 'details', 'category', 'category_id',
            'customer', 'agent', 'status', 'status_display',
            'estimated_price', 'location', 'attachments', 'timeline', 'review',
            'created_at', 'lat', 'lon'
        ]
        read_only_fields = ['id', 'status', 'created_at']

class RequestMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    class Meta:
        model = RequestMessage
        fields = ['id', 'sender_name', 'content', 'created_at']

class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'transaction_type', 'amount', 'note', 'created_at']
