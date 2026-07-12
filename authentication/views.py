# authentication/views.py
import random
import logging
import requests
import jwt
import re
import traceback
from datetime import timedelta

from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, get_user_model
from django.shortcuts import get_object_or_404
from django.utils.timezone import now
from django.conf import settings

from .models import PortfolioImage, AgentProfile, Favorite
from .serializers import (
    RegisterSerializer, TokenResponseSerializer,
    FavoriteSerializer, UserSerializer,
    AgentProfileSerializer, PortfolioItemSerializer
)

logger = logging.getLogger(__name__)
User = get_user_model()

def internal_normalize_phone(phone):
    if not phone: return ''
    digits = ''.join(ch for ch in phone if ch.isdigit())
    if digits.startswith('00964') and len(digits) == 14: return '0' + digits[5:]
    if digits.startswith('964') and len(digits) == 13: return '0' + digits[3:]
    if digits.startswith('7') and len(digits) == 10: return '0' + digits
    return digits

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        phone_raw = request.data.get('phone_number')
        password = request.data.get('password')
        if not phone_raw or not password:
            return Response({"detail": "يرجى إدخال رقم الهاتف وكلمة المرور."}, status=400)
        try:
            phone = internal_normalize_phone(phone_raw)
            # في Django، عندما يكون USERNAME_FIELD هو phone_number، نمرر القيمة في معامل username
            user = authenticate(username=phone, password=password)
            
            if user:
                if not user.is_active: return Response({"detail": "هذا الحساب معطل."}, status=400)
                refresh = RefreshToken.for_user(user)
                return Response({
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "role": getattr(user, 'role', 'customer'),
                    "user": UserSerializer(user, context={'request': request}).data,
                    "detail": "تم تسجيل الدخول بنجاح."
                }, status=200)
            return Response({"detail": "رقم الهاتف أو كلمة المرور غير صحيحة."}, status=401)
        except Exception as e:
            import traceback
            return Response({
                "detail": "خطأ في النظام",
                "error": str(e),
                "traceback": traceback.format_exc()
            }, status=500)

class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid(): return Response({"detail": str(serializer.errors)}, status=400)
        try:
            user = serializer.save()
            tokens = TokenResponseSerializer.get_tokens(user, context={'request': request})
            return Response({"detail": "تم إنشاء الحساب بنجاح", **tokens}, status=201)
        except Exception as e: return Response({"detail": str(e)}, status=500)

class GoogleAuthView(APIView):
    permission_classes = [AllowAny]
    def post(self, request): return Response({"detail": "قيد التطوير"}, status=200)

class SendVerificationCodeView(APIView):
    permission_classes = [AllowAny]
    def post(self, request): return Response({"detail": "قيد التطوير"}, status=200)

class VerifyPhoneView(APIView):
    permission_classes = [AllowAny]
    def post(self, request): return Response({"detail": "قيد التطوير"}, status=200)

class UpdateFcmTokenView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        token = request.data.get('fcm_token')
        request.user.fcm_token = token; request.user.save()
        return Response({"detail": "تم التحديث"})

class ToggleOnlineView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        request.user.is_online = not request.user.is_online; request.user.save()
        return Response({"is_online": request.user.is_online})

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request): return Response(UserSerializer(request.user, context={'request': request}).data)
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid(): serializer.save(); return Response(serializer.data)
        return Response(serializer.errors, status=400)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request): return Response({"detail": "قيد التطوير"}, status=200)

class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request): request.user.delete(); return Response(status=204)

class AgentProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request):
        profile, _ = AgentProfile.objects.get_or_create(user=request.user)
        return Response(AgentProfileSerializer(profile, context={'request': request}).data)

class AgentVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request): return Response({"detail": "تم الإرسال"}, status=200)

class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if not request.user.is_superuser: return Response(status=403)
        profiles = AgentProfile.objects.filter(verification_status='pending')
        return Response(AgentProfileSerializer(profiles, many=True, context={'request': request}).data)

class AdminApproveAgentView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, user_id):
        profile = get_object_or_404(AgentProfile, user_id=user_id)
        profile.verification_status = 'approved'; profile.is_verified = True; profile.save()
        return Response({"detail": "تمت الموافقة"})

class AdminRejectAgentView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, user_id):
        profile = get_object_or_404(AgentProfile, user_id=user_id)
        profile.verification_status = 'rejected'; profile.is_verified = False; profile.save()
        return Response({"detail": "تم الرفض"})

class ChangeRoleView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        role = request.data.get('role')
        if role in ['customer', 'agent']:
            request.user.role = role; request.user.save()
            return Response({"detail": "تم التغيير"})
        return Response(status=400)

class DjangoSessionLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request): return Response(status=200)

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    def post(self, request): return Response(status=200)

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    def post(self, request): return Response(status=200)

class UploadIdentityView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            # الحصول على أو إنشاء AgentProfile
            profile, created = AgentProfile.objects.get_or_create(user=request.user)
            
            # استخراج البيانات المرسلة
            full_name = request.data.get('full_name', '')
            whatsapp_number = request.data.get('whatsapp_number', '')
            profession = request.data.get('profession', 'other')
            custom_profession = request.data.get('custom_profession', '')
            id_card_front = request.FILES.get('id_card_front')
            id_card_back = request.FILES.get('id_card_back')
            
            # التحقق من الصور المطلوبة
            if not id_card_front or not id_card_back:
                return Response(
                    {"detail": "يجب رفع صور وجه وظهر البطاقة"}, 
                    status=400
                )
            
            # تحديث بيانات التوثيق
            if full_name:
                profile.full_name_at_verification = full_name
            if whatsapp_number:
                profile.whatsapp_number = whatsapp_number
            if profession:
                profile.profession = profession
            if custom_profession:
                profile.custom_profession = custom_profession
            
            # حفظ الصور
            profile.id_card_front = id_card_front
            profile.id_card_back = id_card_back
            
            # تعيين حالة التوثيق إلى قيد المراجعة
            profile.verification_status = 'pending'
            profile.save()
            
            return Response({
                "detail": "✅ تم رفع بيانات التوثيق بنجاح، جاري مراجعة الطلب من قبل الإدارة.",
                "profile": AgentProfileSerializer(profile, context={'request': request}).data
            }, status=200)
        except Exception as e:
            logger.error(f"Error in UploadIdentityView: {str(e)}")
            return Response(
                {"detail": f"حدث خطأ: {str(e)}"}, 
                status=500
            )

class AdminAllUsersView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if not request.user.is_superuser: return Response(status=403)
        users = User.objects.all()
        return Response(UserSerializer(users, many=True, context={'request': request}).data)

class AdminStatsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if not request.user.is_superuser: return Response(status=403)
        total_users = User.objects.count()
        verified_agents = AgentProfile.objects.filter(is_verified=True).count()
        pending_verifications = AgentProfile.objects.filter(verification_status='pending').count()
        completed_requests = 0
        pending_requests = 0
        try:
            from services.models import ServiceRequest
            completed_requests = ServiceRequest.objects.filter(status='completed').count()
            pending_requests = ServiceRequest.objects.filter(status='pending').count()
        except Exception:
            pass
        return Response({
            "total_users": total_users,
            "verified_agents": verified_agents,
            "pending_verifications": pending_verifications,
            "completed_requests": completed_requests,
            "pending_requests": pending_requests,
            "new_reports": pending_verifications,
        })

class FavoriteListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        favs = Favorite.objects.filter(user=request.user)
        return Response(FavoriteSerializer(favs, many=True).data)
    def post(self, request):
        agent_id = request.data.get('agent_id')
        agent = get_object_or_404(AgentProfile, id=agent_id)
        Favorite.objects.get_or_create(user=request.user, agent=agent)
        return Response(status=201)

class FavoriteDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, agent_id):
        Favorite.objects.filter(user=request.user, agent_id=agent_id).delete()
        return Response(status=204)

class ProfessionalListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        # تصفية المهنيين الحقيقيين فقط (الموثقين والذين لديهم بيانات كاملة)
        agents = AgentProfile.objects.filter(is_verified=True).exclude(
            profession='other', custom_profession=''
        ).exclude(
            profession='other', custom_profession__isnull=True
        )
        return Response(AgentProfileSerializer(agents, many=True, context={'request': request}).data)

class ProfessionalDetailView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, pk):
        agent = get_object_or_404(AgentProfile, pk=pk)
        from .serializers import ProfessionalDetailSerializer
        return Response(ProfessionalDetailSerializer(agent, context={'request': request}).data)

class CategoryAPIListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        from services.models import Category
        from .serializers import CategorySerializer
        cats = Category.objects.filter(is_active=True)
        return Response(CategorySerializer(cats, many=True).data)

class FeaturedAgentsView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        # تصفية المهنيين الحقيقيين فقط
        agents = AgentProfile.objects.filter(is_verified=True).exclude(
            profession='other', custom_profession=''
        ).exclude(
            profession='other', custom_profession__isnull=True
        )[:10]
        return Response(AgentProfileSerializer(agents, many=True, context={'request': request}).data)

def add_portfolio_image(request):
    """إضافة صورة إلى معرض المندوب"""
    if request.method == 'POST':
        try:
            if not request.user.is_authenticated:
                return Response({"detail": "يجب تسجيل الدخول أولاً"}, status=401)
            
            # الحصول على AgentProfile
            profile = getattr(request.user, 'agent_profile', None)
            if not profile:
                profile = AgentProfile.objects.create(user=request.user)
            
            # استخراج الصورة والعنوان
            image = request.FILES.get('image')
            caption = request.data.get('caption', '')
            
            if not image:
                return Response({"detail": "يرجى اختيار صورة"}, status=400)
            
            # إنشاء صورة جديدة
            portfolio_img = PortfolioImage.objects.create(
                agent_profile=profile,
                image=image,
                caption=caption
            )
            
            return Response({
                "detail": "✅ تمت إضافة الصورة بنجاح",
                "portfolio": PortfolioItemSerializer(portfolio_img).data
            }, status=201)
        except Exception as e:
            logger.error(f"Error adding portfolio image: {str(e)}")
            return Response({"detail": f"حدث خطأ: {str(e)}"}, status=500)
    
    return Response({"detail": "الطريقة غير مدعومة"}, status=405)


def delete_portfolio_image(request, pk):
    """حذف صورة من معرض المندوب"""
    if request.method == 'DELETE':
        try:
            if not request.user.is_authenticated:
                return Response({"detail": "يجب تسجيل الدخول أولاً"}, status=401)
            
            # التحقق من ملكية الصورة
            portfolio_img = get_object_or_404(PortfolioImage, pk=pk)
            if portfolio_img.agent_profile.user != request.user:
                return Response({"detail": "ليس لديك صلاحية لحذف هذه الصورة"}, status=403)
            
            # حذف الصورة
            portfolio_img.delete()
            
            return Response({"detail": "✅ تم حذف الصورة بنجاح"}, status=204)
        except Exception as e:
            logger.error(f"Error deleting portfolio image: {str(e)}")
            return Response({"detail": f"حدث خطأ: {str(e)}"}, status=500)
    
    return Response({"detail": "الطريقة غير مدعومة"}, status=405)
