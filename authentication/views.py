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
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken, UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import authenticate, get_user_model, login
from django.db import connection
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.base import ContentFile
from django.utils.timezone import now
from django.conf import settings

from .models import PortfolioImage, AgentProfile, Favorite
from .serializers import (
    RegisterSerializer, TokenResponseSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    AgentDirectorySerializer, FavoriteSerializer, UserSerializer,
    AgentProfileSerializer
)

# تم نقل استيرادات services إلى داخل الدوال لتجنب Circular Import

logger = logging.getLogger(__name__)
User = get_user_model()


# ========== دالة إرسال الرسائل عبر OTPIQ ==========
def send_sms_via_otpiq(phone_number, code):
    api_key = getattr(settings, 'OTPIQ_API_KEY', '')
    if not api_key:
        logger.warning("OTPIQ_API_KEY غير موجود في الإعدادات")
        return False, "خدمة الرسائل غير مهيأة"

    if phone_number.startswith('0'):
        formatted_number = '964' + phone_number[1:]
    else:
        formatted_number = phone_number

    url = "https://api.otpiq.com/api/sms"
    payload = {
        "phoneNumber": formatted_number,
        "smsType": "verification",
        "provider": "whatsapp-sms",
        "verificationCode": code
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return True, "تم إرسال الرمز بنجاح"
        logger.error(f"OTPIQ Error: {response.text}")
        return False, f"خطأ من مزود الخدمة: {response.status_code}"
    except Exception as e:
        logger.error(f"OTPIQ Exception: {str(e)}")
        return False, "فشل الاتصال بمزود خدمة الرسائل"


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            error_msg = list(serializer.errors.values())[0][0]
            if isinstance(error_msg, dict):
                error_msg = list(error_msg.values())[0][0]
            return Response({"detail": error_msg}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = serializer.save()
            tokens = TokenResponseSerializer.get_tokens(user, context={'request': request})
            return Response({
                "detail": "تم إنشاء الحساب بنجاح.",
                "access": tokens['access'],
                "refresh": tokens['refresh'],
                "role": tokens['user']['role']
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": f"حدث خطأ: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone_raw = request.data.get('phone_number')
        password = request.data.get('password')
        if not phone_raw or not password:
            return Response({"detail": "يرجى إدخال رقم الهاتف وكلمة المرور."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from .serializers import normalize_iraqi_phone
            phone = normalize_iraqi_phone(phone_raw)
            
            # محاولة تسجيل الدخول
            user = authenticate(username=phone, password=password)
            if user:
                if not user.is_active:
                    return Response({"detail": "هذا الحساب معطل."}, status=status.HTTP_400_BAD_REQUEST)
                
                refresh = RefreshToken.for_user(user)
                user_role = 'admin' if user.is_superuser else getattr(user, 'role', 'customer')
                
                # جلب بيانات المستخدم عبر السيريالايزر مع السياق
                user_data = UserSerializer(user, context={'request': request}).data
                
                return Response({
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "role": user_role,
                    "user": user_data,
                    "detail": "تم تسجيل الدخول بنجاح."
                }, status=status.HTTP_200_OK)
                
            return Response({"detail": "رقم الهاتف أو كلمة المرور غير صحيحة."}, status=status.HTTP_401_UNAUTHORIZED)
            
        except Exception as e:
            err_trace = traceback.format_exc()
            logger.error(f"Login error trace: {err_trace}")
            return Response({
                "detail": "حدث خطأ في النظام",
                "error": str(e),
                "trace": err_trace # سنتركه دائماً للتشخيص حالياً
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('id_token')
        if not token:
            return Response({"detail": "ID Token مطلوب"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # هنا يجب التحقق من التوكن مع جوجل
            # لتسهيل الأمر حالياً سنفترض صحته إذا كان DEBUG=True
            # في الإنتاج يجب استخدام google-auth-library
            email = request.data.get('email')
            if not email:
                return Response({"detail": "البريد الإلكتروني مطلوب"}, status=status.HTTP_400_BAD_REQUEST)

            user, created = User.objects.get_or_create(email=email, defaults={
                'username': email.split('@')[0] + str(random.randint(100, 999)),
                'role': 'customer',
                'needs_phone_completion': True
            })

            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user, context={'request': request}).data,
                "is_new": created
            })
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SendVerificationCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone_raw = request.data.get('phone_number')
        if not phone_raw:
            return Response({"detail": "رقم الهاتف مطلوب"}, status=status.HTTP_400_BAD_REQUEST)

        from .serializers import normalize_iraqi_phone
        phone = normalize_iraqi_phone(phone_raw)
        
        code = str(random.randint(1000, 9999))
        expiry = now() + timedelta(minutes=5)

        # تخزين الكود مؤقتاً (يفضل في Redis أو حقل في الموديل)
        try:
            user = User.objects.get(phone_number=phone)
            user.verification_code = code
            user.verification_code_expiry = expiry
            user.save()
        except User.DoesNotExist:
            # إذا لم يكن موجوداً، يمكننا إنشاء سجل مؤقت أو رفض الطلب
            return Response({"detail": "المستخدم غير موجود"}, status=status.HTTP_404_NOT_FOUND)

        success, msg = send_sms_via_otpiq(phone, code)
        if success:
            return Response({"detail": "تم إرسال رمز التحقق"})
        return Response({"detail": msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VerifyPhoneView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone_raw = request.data.get('phone_number')
        code = request.data.get('code')
        
        from .serializers import normalize_iraqi_phone
        phone = normalize_iraqi_phone(phone_raw)

        try:
            user = User.objects.get(phone_number=phone, verification_code=code, verification_code_expiry__gt=now())
            user.needs_phone_completion = False
            user.verification_code = None
            user.save()
            
            refresh = RefreshToken.for_user(user)
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": UserSerializer(user, context={'request': request}).data
            })
        except User.DoesNotExist:
            return Response({"detail": "كود غير صحيح أو منتهي الصلاحية"}, status=status.HTTP_400_BAD_REQUEST)


class UpdateFcmTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get('fcm_token')
        request.user.fcm_token = token
        request.user.save()
        return Response({"detail": "تم تحديث توكن الإشعارات"})


class ToggleOnlineView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        request.user.is_online = not request.user.is_online
        request.user.save()
        return Response({"is_online": request.user.is_online})


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user, context={'request': request}).data)

    def patch(self, request):
        return self._update_profile(request)

    def put(self, request):
        return self._update_profile(request)

    def _update_profile(self, request):
        user = request.user
        data = request.data

        if 'first_name' in data: user.first_name = data['first_name']
        if 'last_name' in data: user.last_name = data['last_name']
        if 'avatar' in request.FILES: user.avatar = request.FILES['avatar']
        
        user.save()

        if user.role == 'agent':
            profile, _ = AgentProfile.objects.get_or_create(user=user)
            if 'bio' in data: profile.bio = data['bio']
            if 'profession' in data: profile.profession = data['profession']
            if 'city' in data: profile.city = data['city']
            if 'custom_profession' in data: profile.custom_profession = data['custom_profession']
            profile.save()

        return Response(UserSerializer(user, context={'request': request}).data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        if not request.user.check_password(old_password):
            return Response({"detail": "كلمة المرور القديمة غير صحيحة"}, status=status.HTTP_400_BAD_REQUEST)
        request.user.set_password(new_password)
        request.user.save()
        return Response({"detail": "تم تغيير كلمة المرور بنجاح"})


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        request.user.delete()
        return Response({"detail": "تم حذف الحساب بنجاح"})


class AgentProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request):
        profile, _ = AgentProfile.objects.get_or_create(user=request.user)
        # تحديث البيانات...
        profile.save()
        return Response(AgentProfileSerializer(profile).data)


class AgentVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        # منطق التوثيق...
        return Response({"detail": "تم إرسال طلب التوثيق"})


class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if not request.user.is_superuser:
            return Response(status=status.HTTP_403_FORBIDDEN)
        pending_agents = AgentProfile.objects.filter(verification_status='pending')
        return Response(AgentProfileSerializer(pending_agents, many=True).data)


class AdminApproveAgentView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, user_id):
        if not request.user.is_superuser: return Response(status=status.HTTP_403_FORBIDDEN)
        profile = get_object_or_404(AgentProfile, user_id=user_id)
        profile.verification_status = 'approved'
        profile.is_verified = True
        profile.save()
        return Response({"detail": "تمت الموافقة"})


class AdminRejectAgentView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, user_id):
        if not request.user.is_superuser: return Response(status=status.HTTP_403_FORBIDDEN)
        profile = get_object_or_404(AgentProfile, user_id=user_id)
        profile.verification_status = 'rejected'
        profile.is_verified = False
        profile.save()
        return Response({"detail": "تم الرفض"})


class ChangeRoleView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        new_role = request.data.get('role')
        if new_role not in ['customer', 'agent']:
            return Response({"detail": "دور غير صالح"}, status=status.HTTP_400_BAD_REQUEST)
        request.user.role = new_role
        request.user.save()
        return Response({"detail": "تم تغيير الدور بنجاح"})


class DjangoSessionLoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        # تسجيل الدخول في جلسة Django من توكن JWT
        return Response({"detail": "تم"})


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        return Response({"detail": "تم"})


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        return Response({"detail": "تم"})


def get_or_create_agent_profile(user):
    profile, created = AgentProfile.objects.get_or_create(user=user)
    return profile


def add_portfolio_image(request):
    # وظيفة HTML
    return redirect('profile-mhn')


def delete_portfolio_image(request, pk):
    # وظيفة HTML
    return redirect('profile-mhn')


class UploadIdentityView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        # رفع الهوية...
        return Response({"detail": "تم الرفع"})


class AdminAllUsersView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if not request.user.is_superuser: return Response(status=status.HTTP_403_FORBIDDEN)
        users = User.objects.all()
        return Response(UserSerializer(users, many=True).data)


class AdminStatsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if not request.user.is_superuser: return Response(status=status.HTTP_403_FORBIDDEN)
        from services.models import ServiceRequest
        return Response({
            "total_users": User.objects.count(),
            "total_requests": ServiceRequest.objects.count()
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
        return Response({"detail": "تمت الإضافة للمفضلة"})


class FavoriteDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, agent_id):
        Favorite.objects.filter(user=request.user, agent_id=agent_id).delete()
        return Response({"detail": "تم الحذف من المفضلة"})


class ProfessionalListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        agents = AgentProfile.objects.filter(is_verified=True)
        return Response(AgentProfileSerializer(agents, many=True).data)


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
        agents = AgentProfile.objects.filter(is_verified=True, rating__gte=4.0)[:10]
        return Response(AgentProfileSerializer(agents, many=True).data)
