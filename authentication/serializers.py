import re
import logging
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, AgentProfile, Favorite, PortfolioImage

logger = logging.getLogger(__name__)

def normalize_iraqi_phone(phone):
    if not phone: return ''
    phone_str = str(phone)
    digits = ''.join(ch for ch in phone_str if ch.isdigit())
    if digits.startswith('00964') and len(digits) == 14: return '0' + digits[5:]
    if digits.startswith('964') and len(digits) == 13: return '0' + digits[3:]
    if digits.startswith('7') and len(digits) == 10: return '0' + digits
    return digits

class PortfolioItemSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = PortfolioImage
        fields = ['id', 'caption', 'image', 'uploaded_at']
    
    def get_image(self, obj):
        try:
            if obj.image and hasattr(obj.image, 'url'):
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.image.url)
                return f"https://njazzz.pythonanywhere.com{obj.image.url}"
        except:
            pass
        return None

class AgentProfileSerializer(serializers.ModelSerializer):
    id_card_front = serializers.SerializerMethodField()
    id_card_back = serializers.SerializerMethodField()
    profession_display = serializers.SerializerMethodField()
    portfolio_images = serializers.SerializerMethodField()
    full_name = serializers.ReadOnlyField(source='user.full_name')
    phone_number = serializers.ReadOnlyField(source='user.phone_number')
    user_id = serializers.ReadOnlyField(source='user.id')
    
    # حقول إضافية للتوافق مع ProfessionalListModel في Flutter
    avg_rating = serializers.FloatField(source='rating', read_only=True)
    total_reviews = serializers.IntegerField(source='total_jobs', read_only=True)
    profile_photo = serializers.SerializerMethodField()
    is_online = serializers.BooleanField(source='user.is_online', read_only=True)

    class Meta:
        model = AgentProfile
        fields = [
            'id', 'user_id', 'full_name', 'phone_number', 'bio', 
            'is_verified', 'verification_status', 'balance', 'rating', 
            'avg_rating', 'total_jobs', 'total_reviews', 'profile_photo',
            'is_online', 'id_card_front', 'id_card_back', 'profession', 
            'custom_profession', 'city', 'whatsapp_number', 
            'full_name_at_verification', 'profession_display', 'portfolio_images'
        ]

    def get_profile_photo(self, obj):
        try:
            if obj.user.avatar and hasattr(obj.user.avatar, 'url'):
                request = self.context.get('request')
                if request: return request.build_absolute_uri(obj.user.avatar.url)
                return f"https://njazzz.pythonanywhere.com{obj.user.avatar.url}"
        except: pass
        return None

    def get_profession_display(self, obj):
        return obj.get_profession_display()

    def get_id_card_front(self, obj):
        try:
            if obj.id_card_front and hasattr(obj.id_card_front, 'url'):
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.id_card_front.url)
                return f"https://njazzz.pythonanywhere.com{obj.id_card_front.url}"
        except:
            pass
        return None

    def get_id_card_back(self, obj):
        try:
            if obj.id_card_back and hasattr(obj.id_card_back, 'url'):
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.id_card_back.url)
                return f"https://njazzz.pythonanywhere.com{obj.id_card_back.url}"
        except:
            pass
        return None
    
    def get_portfolio_images(self, obj):
        """إرجاع صور المعرض مع URLs كاملة"""
        images = obj.portfolio_images.all()
        return PortfolioItemSerializer(images, many=True, context=self.context).data

class CategorySerializer(serializers.ModelSerializer):
    name_ar = serializers.CharField(source='name')
    class Meta:
        from services.models import Category
        model = Category
        fields = ['id', 'name_ar', 'icon', 'description', 'order']

class ReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='reviewer.full_name')
    class Meta:
        from services.models import Review
        model = Review
        fields = ['id', 'customer_name', 'rating', 'comment', 'created_at']

class UserSerializer(serializers.ModelSerializer):
    agent_profile = serializers.SerializerMethodField()
    profile_photo = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    total_requests = serializers.SerializerMethodField()
    pending_requests = serializers.SerializerMethodField()
    is_verified = serializers.SerializerMethodField()
    verification_status = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'phone_number', 'full_name', 'role', 'profile_photo', 'avatar',
            'is_online', 'agent_profile', 'wallet_balance',
            'total_requests', 'pending_requests', 'is_verified', 'verification_status',
            'is_customer_verified', 'customer_rating', 'customer_total_reviews',
            'is_profile_complete', 'needs_phone_completion'
        ]
        extra_kwargs = {
            'avatar': {'write_only': True}
        }

    def get_role(self, obj):
        if obj.is_superuser: return 'admin'
        return getattr(obj, 'role', 'customer')

    def get_full_name(self, obj):
        fname = obj.first_name or ''
        lname = obj.last_name or ''
        name = f"{fname} {lname}".strip()
        return name if name else obj.phone_number

    def get_profile_photo(self, obj):
        try:
            if obj.avatar and hasattr(obj.avatar, 'url'):
                request = self.context.get('request')
                if request: return request.build_absolute_uri(obj.avatar.url)
                return f"https://njazzz.pythonanywhere.com{obj.avatar.url}"
        except: pass
        return None

    def get_agent_profile(self, obj):
        try:
            profile = getattr(obj, 'agent_profile', None)
            if profile:
                return AgentProfileSerializer(profile, context=self.context).data
        except: pass
        return None

    def get_total_requests(self, obj):
        from services.models import ServiceRequest
        if obj.role == 'agent':
            return ServiceRequest.objects.filter(agent=obj).count()
        return ServiceRequest.objects.filter(customer=obj).count()

    def get_pending_requests(self, obj):
        from services.models import ServiceRequest
        if obj.role == 'agent':
            return ServiceRequest.objects.filter(agent=obj, status='in_progress').count()
        return ServiceRequest.objects.filter(customer=obj, status='pending').count()

    def get_is_verified(self, obj):
        profile = getattr(obj, 'agent_profile', None)
        return profile.is_verified if profile else False

    def get_verification_status(self, obj):
        profile = getattr(obj, 'agent_profile', None)
        return profile.verification_status if profile else None

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    profession = serializers.CharField(write_only=True, required=False)
    custom_profession = serializers.CharField(write_only=True, required=False)
    full_name = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['phone_number', 'first_name', 'last_name', 'full_name', 'role', 'password', 'password_confirm', 'profession', 'custom_profession']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("كلمة المرور غير متطابقة")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        profession = validated_data.pop('profession', None)
        custom_profession = validated_data.pop('custom_profession', None)
        password = validated_data.pop('password')
        full_name = validated_data.pop('full_name', None)
        
        first_name = validated_data.get('first_name', '')
        last_name = validated_data.get('last_name', '')
        
        if full_name and not first_name:
            parts = full_name.strip().split(' ')
            first_name = parts[0]
            last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''

        # ✅ تمرير كلمة المرور مباشرة إلى create_user لتشفيرها مرة واحدة فقط
        user = User.objects.create_user(
            phone_number=validated_data.get('phone_number'),
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=validated_data.get('role', 'customer'),
        )
        
        if user.role == 'agent' or profession:
            AgentProfile.objects.create(
                user=user, 
                profession=profession or 'other',
                custom_profession=custom_profession
            )
        return user

class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
    @staticmethod
    def get_tokens(user, context=None):
        refresh = RefreshToken.for_user(user)
        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user, context=context).data
        }

class ProfessionalSerializer(serializers.ModelSerializer):
    # استخدام حقول مباشرة بدلاً من UserSerializer بالكامل لتجنب التعليق
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    profile_photo = serializers.SerializerMethodField()
    phone_number = serializers.CharField(source='user.phone_number', read_only=True)
    is_online = serializers.BooleanField(source='user.is_online', read_only=True)
    
    title = serializers.CharField(source='get_profession_display', read_only=True)
    profession_display = serializers.CharField(source='get_profession_display', read_only=True)

    class Meta:
        model = AgentProfile
        fields = [
            'id', 'full_name', 'profile_photo', 'phone_number', 'is_online',
            'title', 'profession_display', 'city', 'rating', 'total_jobs'
        ]

    def get_profile_photo(self, obj):
        try:
            if obj.user.avatar and hasattr(obj.user.avatar, 'url'):
                request = self.context.get('request')
                if request: return request.build_absolute_uri(obj.user.avatar.url)
                return f"https://njazzz.pythonanywhere.com{obj.user.avatar.url}"
        except: pass
        return None

class ProfessionalDetailSerializer(ProfessionalSerializer):
    portfolio_images = PortfolioItemSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    
    class Meta(ProfessionalSerializer.Meta):
        fields = ProfessionalSerializer.Meta.fields + ['portfolio_images', 'reviews']

    def get_reviews(self, obj):
        from services.models import Review
        reviews = Review.objects.filter(reviewee=obj.user, review_type='to_agent').order_by('-created_at')[:10]
        return ReviewSerializer(reviews, many=True).data

class FavoriteSerializer(serializers.ModelSerializer):
    agent = AgentProfileSerializer()
    class Meta:
        model = Favorite
        fields = ['id', 'agent', 'created_at']
