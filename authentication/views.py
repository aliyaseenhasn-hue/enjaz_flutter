# authentication/views.py
import random
import logging
import requests
import jwt
import re
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

logger = logging.getLogger(__name__)
User = get_user_model()

def send_sms_via_otpiq(phone_number, code):
    api_key = getattr(settings, 'OTPIQ_API_KEY', '')
    if not api_key: return False, "خدمة الرسائل غير مهيأة"
    formatted_number = '964' + phone_number[1:] if phone_number.startswith('0') else phone_number
    url = "https://api.otpiq.com/api/sms"
    payload = {"phoneNumber": formatted_number, "smsType": "verification", "provider": "whatsapp-sms", "verificationCode": code}
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return (True, "تم") if response.status_code == 200 else (False, "فشل الإرسال")
    except: return False, "خطأ اتصال"

class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = serializer.save()
            tokens = TokenResponseSerializer.get_tokens(user, context={'request': request})
            return Response({"detail": "تم إنشاء الحساب", **tokens}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        phone_raw = request.data.get('phone_number')
        password = request.data.get('password')
        if not phone_raw or not password:
            return Response({"detail": "يرجى إدخال البيانات"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            from .serializers import normalize_iraqi_phone
            phone = normalize_iraqi_phone(phone_raw)
            user = authenticate(username=phone, password=password)
            if user:
                if not user.is_active: return Response({"detail": "الحساب معطل"}, status=status.HTTP_400_BAD_REQUEST)
                refresh = RefreshToken.for_user(user)
                user_data = UserSerializer(user, context={'request': request}).data
                return Response({
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "role": getattr(user, 'role', 'customer'),
                    "user": user_data,
                    "detail": "تم تسجيل الدخول"
                }, status=status.HTTP_200_OK)
            return Response({"detail": "رقم الهاتف أو كلمة المرور غير صحيحة"}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.exception("Login Crash")
            return Response({"detail": "خطأ داخلي في الخادم", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UpdateFcmTokenView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        token = request.data.get('fcm_token')
        if token:
            request.user.fcm_token = token
            request.user.save()
        return Response({"detail": "تم التحديث"})

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(UserSerializer(request.user, context={'request': request}).data)
    def patch(self, request):
        user = request.user
        for attr, value in request.data.items():
            if hasattr(user, attr) and attr not in ['id', 'phone_number']:
                setattr(user, attr, value)
        user.save()
        return Response(UserSerializer(user, context={'request': request}).data)

class ProfessionalListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        agents = AgentProfile.objects.filter(is_verified=True)
        return Response(AgentProfileSerializer(agents, many=True).data)

class CategoryAPIListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        from services.models import Category
        from .serializers import CategorySerializer
        cats = Category.objects.filter(is_active=True)
        return Response(CategorySerializer(cats, many=True).data)

# ... باقي الـ Views يمكن إضافتها لاحقاً عند الحاجة لتقليل حجم الملف حالياً لضمان الاستقرار
