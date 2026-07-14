from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()

from .models import (
    Category, RequestAttachment, RequestMessage,
    RequestTimeline, Review, ServiceRequest, WalletTransaction,
)
from authentication.models import AgentProfile, PortfolioImage


class PortfolioImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    class Meta:
        model = PortfolioImage
        fields = ['id', 'image', 'caption', 'uploaded_at']

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            # Fallback for production if domain is known
            url = obj.image.url
            if not url.startswith('http'):
                return f"https://njazzz.pythonanywhere.com{url}"
            return url
        return None


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
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return f"https://njazzz.pythonanywhere.com{obj.avatar.url}"
        return None


class AgentProfileListSerializer(serializers.ModelSerializer):
    """
    Serializer لعرض قائمة المهنيين (لائحة مختصرة)
    """
    name = serializers.CharField(source='user.full_name', read_only=True)
    avatar = serializers.SerializerMethodField()
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    profession_display = serializers.SerializerMethodField()
    profession = serializers.CharField(read_only=True)
    reviews_count = serializers.SerializerMethodField()
    is_available = serializers.BooleanField(source='user.is_online', read_only=True)
    distance = serializers.FloatField(read_only=True, default=None)

    class Meta:
        model = AgentProfile
        fields = [
            'id', 'name', 'avatar', 'phone_number', 'profession',
            'profession_display', 'bio', 'rating', 'reviews_count',
            'city', 'service_min_price', 'service_max_price',
            'is_verified', 'is_available', 'distance',
            'lat', 'lon',
        ]

    def get_avatar(self, obj):
        if obj.user.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.avatar.url)
            return f"https://njazzz.pythonanywhere.com{obj.user.avatar.url}"
        return None

    def get_profession_display(self, obj):
        return obj.get_profession_display()

    def get_reviews_count(self, obj):
        return getattr(obj, 'reviews_count_cached', 0)


class AgentProfileDetailSerializer(serializers.ModelSerializer):
    """
    Serializer لعرض التفاصيل الكاملة للمهني
    """
    name = serializers.CharField(source='user.full_name', read_only=True)
    avatar = serializers.SerializerMethodField()
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    profession_display = serializers.SerializerMethodField()
    profession = serializers.CharField(read_only=True)
    reviews_count = serializers.SerializerMethodField()
    is_available = serializers.BooleanField(source='user.is_online', read_only=True)
    distance = serializers.FloatField(read_only=True, default=None)
    portfolio_images = PortfolioImageSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    whatsapp_number = serializers.CharField(read_only=True)
    total_jobs = serializers.IntegerField(read_only=True)
    verification_status = serializers.CharField(read_only=True)

    class Meta:
        model = AgentProfile
        fields = [
            'id', 'name', 'avatar', 'phone_number', 'profession',
            'profession_display', 'bio', 'rating', 'reviews_count',
            'city', 'service_min_price', 'service_max_price',
            'is_verified', 'verification_status', 'is_available',
            'distance', 'lat', 'lon', 'whatsapp_number',
            'total_jobs', 'portfolio_images', 'reviews'
        ]

    def get_avatar(self, obj):
        if obj.user.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.avatar.url)
            return f"https://njazzz.pythonanywhere.com{obj.user.avatar.url}"
        return None

    def get_profession_display(self, obj):
        return obj.get_profession_display()

    def get_reviews_count(self, obj):
        return getattr(obj, 'reviews_count_cached', 0)

    def get_reviews(self, obj):
        # جلب آخر 10 تقييمات للمهني
        reviews = Review.objects.filter(reviewee=obj.user, review_type='to_agent').order_by('-created_at')[:10]
        return ReviewSerializer(reviews, many=True).data


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
    customer = SimpleUserSerializer(read_only=True)
    agent = SimpleUserSerializer(read_only=True)

    def get_category_name(self, obj):
        return obj.category.name if obj.category else ""

    class Meta:
        model = ServiceRequest
        fields = [
            'id', 'title', 'details', 'category_name', 'customer', 'agent',
            'status', 'status_display', 'created_at', 'location',
            'estimated_price', 'lat', 'lon'
        ]

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