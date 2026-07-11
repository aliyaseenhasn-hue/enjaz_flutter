import re
import logging
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User, AgentProfile, Favorite, PortfolioImage

logger = logging.getLogger(__name__)

def normalize_iraqi_phone(phone):
    if not phone: return ''
    digits = ''.join(ch for ch in phone if ch.isdigit())
    if digits.startswith('00964') and len(digits) == 14: return '0' + digits[5:]
    if digits.startswith('964') and len(digits) == 13: return '0' + digits[3:]
    if digits.startswith('7') and len(digits) == 10: return '0' + digits
    return digits

class AgentProfileSerializer(serializers.ModelSerializer):
    id_card_front = serializers.SerializerMethodField()
    id_card_back = serializers.SerializerMethodField()
    profession_display = serializers.SerializerMethodField()
    portfolio_images = serializers.SerializerMethodField()

    class Meta:
        model = AgentProfile
        fields = [
            'id', 'bio', 'is_verified', 'verification_status', 
            'balance', 'rating', 'total_jobs', 'id_card_front', 
            'id_card_back', 'profession', 'custom_profession', 'city',
            'whatsapp_number', 'full_name_at_verification', 'profession_display',
            'portfolio_images'
        ]

    def get_profession_display(self, obj):
        return obj.get_profession_display()

    def get_id_card_front(self, obj):
        try:
            if obj.id_card_front and hasattr(obj.id_card_front, 'url'):
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.id_card_front.url)
                return obj.id_card_front.url
        except:
            pass
        return None

    def get_id_card_back(self, obj):
        try:
            if obj.id_card_back and hasattr(obj.id_card_back, 'url'):
                request = self.context.get('request')
                if request:
                    return request.build_absolute_uri(obj.id_card_back.url)
                return obj.id_card_back.url
        except:
            pass
        return None
    
    def get_portfolio_images(self, obj):
        """إرجاع صور المعرض مع URLs كاملة"""
        images = obj.portfolio_images.all()
        return PortfolioItemSerializer(images, many=True, context=self.context).data

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
            'id', 'phone_number', 'full_name', 'role', 'profile_photo', 
            'is_online', 'agent_profile', 'wallet_balance', 
            'total_requests', 'pending_requests', 'is_verified', 'verification_status'
        ]

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
                return obj.avatar.url
        except: pass
        return None

    def get_agent_profile(self, obj):
        try:
            profile = getattr(obj, 'agent_profile', None)
            if profile:
                # نمرر الـ context لضمان بناء روابط الصور بشكل كامل
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
    class Meta:
        model = User
        fields = ['phone_number', 'first_name', 'last_name', 'role', 'password', 'password_confirm']
    def validate(self, data):
        if data['password'] != data['password_confirm']: raise serializers.ValidationError("كلمة المرور غير متطابقة")
        return data
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
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

class CategorySerializer(serializers.ModelSerializer):
    name_ar = serializers.CharField(source='name')
    class Meta:
        from services.models import Category
        model = Category
        fields = ['id', 'name_ar', 'icon', 'description', 'order']

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
                # إذا لم يكن هناك request، إرجع الـ URL النسبي على الأقل
                return obj.image.url
        except:
            pass
        return None

class ProfessionalSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    title = serializers.CharField(source='get_profession_display', read_only=True)
    class Meta:
        model = AgentProfile
        fields = ['id', 'user', 'title', 'city', 'rating', 'total_jobs']

class ProfessionalDetailSerializer(ProfessionalSerializer):
    portfolio_images = PortfolioItemSerializer(many=True, read_only=True)
    class Meta(ProfessionalSerializer.Meta):
        fields = ProfessionalSerializer.Meta.fields + ['portfolio_images']

class FavoriteSerializer(serializers.ModelSerializer):
    agent = AgentProfileSerializer()
    class Meta:
        model = Favorite
        fields = ['id', 'agent', 'created_at']
