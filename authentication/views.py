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
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    AgentDirectorySerializer, FavoriteSerializer, UserSerializer,
    AgentProfileSerializer, PortfolioItemSerializer
)

logger = logging.getLogger(__name__)
User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = serializer.save()
            tokens = TokenResponseSerializer.get_tokens(user, context={'request': request})
            return Response({"detail": "تم إنشاء الحساب بنجاح", **tokens}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
            user = authenticate(phone_number=phone, password=password)
            if not user:
                user = authenticate(username=phone, password=password)
            
            if user:
                if not user.is_active: return Response({"detail": "هذا الحساب معطل."}, status=status.HTTP_400_BAD_REQUEST)
                refresh = RefreshToken.for_user(user)
                return Response({
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "role": getattr(user, 'role', 'customer'),
                    "user": UserSerializer(user, context={'request': request}).data,
                    "detail": "تم تسجيل الدخول بنجاح."
                }, status=status.HTTP_200_OK)
            return Response({"detail": "رقم الهاتف أو كلمة المرور غير صحيحة."}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response({"detail": "خطأ في النظام", "error": str(e), "trace": traceback.format_exc()}, status=500)

class GoogleAuthView(APIView):
    permission_classes = [AllowAny]
    def post(self, request): return Response({"detail": "قيد التنفيذ"}, status=200)

class SendVerificationCodeView(APIView):
    permission_classes = [AllowAny]
    def post(self, request): return Response({"detail": "قيد التنفيذ"}, status=200)

class VerifyPhoneView(APIView):
    permission_classes = [AllowAny]
    def post(self, request): return Response({"detail": "قيد التنفيذ"}, status=200)

class UpdateFcmTokenView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        token = request.data.get('fcm_token')
        request.user.fcm_token = token
        request.user.save()
        return Response({"detail": "تم التحديث"})

class ToggleOnlineView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        request.user.is_online = not request.user.is_online
        request.user.save()
        return Response({"is_online": request.user.is_online})

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request): return Response(UserSerializer(request.user, context={'request': request}).data)
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request): return Response({"detail": "قيد التنفيذ"}, status=200)

class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request):
        request.user.delete()
        return Response(status=204)

class AgentProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def put(self, request):
        profile, _ = AgentProfile.objects.get_or_create(user=request.user)
        return Response(AgentProfileSerializer(profile).data)

class AgentVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request): return Response({"detail": "تم الإرسال"}, status=200)

class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        if not request.user.is_superuser: return Response(status=403)
        profiles = AgentProfile.objects.filter(verification_status='pending')
        return Response(AgentProfileSerializer(profiles, many=True).data)

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
    def post(self, request): return Response(status=200)

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
        return Response({"users": User.objects.count()})

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
        agents = AgentProfile.objects.filter(is_verified=True)[:10]
        return Response(AgentProfileSerializer(agents, many=True).data)

def add_portfolio_image(request): return Response(status=200)
def delete_portfolio_image(request, pk): return Response(status=200)
