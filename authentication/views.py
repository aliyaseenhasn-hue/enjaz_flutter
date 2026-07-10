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
    CategorySerializer
)

from services.models import ServiceRequest, RequestMessage, Review, WalletTransaction, RequestTimeline, RequestAttachment
from notifications.models import Notification
from .forms import PortfolioImageForm

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
        if response.ok:
            return True, "تم الإرسال"
        else:
            logger.error(f"OTPIQ responded with {response.status_code}: {response.text}")
            return False, f"خطأ من مزود الخدمة: {response.status_code}"
    except Exception as e:
        logger.exception(f"فشل إرسال الرسالة: {e}")
        return False, str(e)


# ========== كلاسات API ==========

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

        from .serializers import normalize_iraqi_phone
        phone = normalize_iraqi_phone(phone_raw)

        try:
            user = authenticate(username=phone, password=password)
            if user:
                if not user.is_active:
                    return Response({"detail": "هذا الحساب معطل."}, status=status.HTTP_400_BAD_REQUEST)
                refresh = RefreshToken.for_user(user)
                user_role = 'admin' if user.is_superuser else getattr(user, 'role', 'customer')
                return Response({
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "role": user_role,
                    "user": UserSerializer(user, context={'request': request}).data,
                    "detail": "تم تسجيل الدخول بنجاح."
                }, status=status.HTTP_200_OK)
            return Response({"detail": "رقم الهاتف أو كلمة المرور غير صحيحة."}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return Response({"detail": f"حدث خطأ في النظام: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        id_token = request.data.get('code') or request.data.get('token')
        if not id_token:
            return Response({"detail": "رمز التوثيق مفقود"}, status=400)

        try:
            google_response = requests.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}")
            if google_response.status_code != 200:
                logger.warning(f"Google tokeninfo failed: status={google_response.status_code}")
                return Response({"detail": "رمز غير صالح"}, status=400)

            user_data = google_response.json()
            email = user_data.get('email')
            name = user_data.get('name', '')
            picture = user_data.get('picture')

            user = User.objects.filter(email=email).first()
            if not user:
                temp_phone = f"99{email[:10].replace('.', '')}"
                if User.objects.filter(phone_number=temp_phone).exists():
                    temp_phone = temp_phone + "0"

                name_parts = name.split()
                first_name = name_parts[0] if name_parts else ''
                last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

                user = User.objects.create_user(
                    phone_number=temp_phone,
                    password=None,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    role='customer',
                    needs_phone_completion=True
                )
                user.set_unusable_password()
                user.save()

                if picture:
                    try:
                        img_resp = requests.get(picture)
                        if img_resp.status_code == 200:
                            user.avatar.save(f"avatar_{user.id}.jpg", ContentFile(img_resp.content), save=True)
                    except:
                        pass
            else:
                name_parts = name.split()
                user.first_name = name_parts[0] if name_parts else user.first_name
                user.last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else user.last_name
                if picture and not user.avatar:
                    try:
                        img_resp = requests.get(picture)
                        if img_resp.status_code == 200:
                            user.avatar.save(f"avatar_{user.id}.jpg", ContentFile(img_resp.content), save=True)
                    except:
                        pass
                if user.phone_number.startswith('99'):
                    user.needs_phone_completion = True
                user.save()

            refresh = RefreshToken.for_user(user)
            user_role = 'admin' if user.is_superuser else user.role
            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "role": user_role,
                "user": UserSerializer(user, context={'request': request}).data
            })
        except Exception as e:
            logger.exception(e)
            return Response({"detail": f"خطأ في المصادقة: {str(e)}"}, status=500)


class SendVerificationCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        phone_number = request.data.get('phone_number')
        if not phone_number:
            return Response({"detail": "رقم الهاتف مطلوب"}, status=400)

        from .serializers import normalize_iraqi_phone
        phone = normalize_iraqi_phone(phone_number)
        if not re.match(r'^07[3456789]\d{8}$', phone):
            return Response({"detail": "رقم الهاتف غير صحيح"}, status=400)

        user = request.user
        user.temp_phone = phone
        user.save(update_fields=['temp_phone'])

        code = f"{random.randint(100000, 999999)}"
        user.verification_code = code
        user.verification_code_expiry = now() + timedelta(minutes=5)
        user.save(update_fields=['verification_code', 'verification_code_expiry'])

        success, msg = send_sms_via_otpiq(phone, code)
        if success:
            return Response({"detail": "تم إرسال رمز التحقق عبر واتساب"})
        else:
            return Response({"detail": "فشل إرسال الرسالة، حاول مرة أخرى"}, status=500)


class VerifyPhoneView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get('code')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if not code:
            return Response({"detail": "الرمز مطلوب"}, status=400)

        user = request.user
        if not user.verification_code or user.verification_code != code:
            return Response({"detail": "الرمز غير صحيح"}, status=400)
        if user.verification_code_expiry and user.verification_code_expiry < now():
            return Response({"detail": "انتهت صلاحية الرمز"}, status=400)

        if new_password:
            if len(new_password) < 6:
                return Response({"detail": "كلمة المرور يجب أن تكون 6 أحرف على الأقل"}, status=400)
            if new_password != confirm_password:
                return Response({"detail": "كلمتا المرور غير متطابقتين"}, status=400)
            user.set_password(new_password)

        if hasattr(user, 'temp_phone') and user.temp_phone:
            user.phone_number = user.temp_phone
            user.username = user.temp_phone
            user.temp_phone = None
            user.needs_phone_completion = False
            user.verification_code = None
            user.verification_code_expiry = None
            user.save()
            return Response({"detail": "تم توثيق رقم الهاتف وتعيين كلمة المرور بنجاح"})

        return Response({"detail": "لا يوجد رقم هاتف مؤقت"}, status=400)


class UpdateFcmTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        token = request.data.get('fcm_token')
        if not token:
            return Response({"detail": "FCM token missing"}, status=400)
        request.user.fcm_token = token
        request.user.save(update_fields=['fcm_token'])
        return Response({"detail": "FCM token updated"})


class ToggleOnlineView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user.is_online = not user.is_online
        if user.is_online:
            user.last_seen = now()
        user.save(update_fields=['is_online', 'last_seen'])
        return Response({
            "is_online": user.is_online,
            "detail": "تم تحديث حالة الاتصال بنجاح"
        })


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)

    def patch(self, request):
        return self._update_profile(request)

    def put(self, request):
        return self._update_profile(request)

    def _update_profile(self, request):
        user = request.user
        data = request.data

        logger.info(f"Updating profile for user: {user.phone_number}")

        # معالجة رفع الصورة الشخصية بشكل خاص لضمان استقرارها
        if 'avatar' in request.FILES:
            try:
                user.avatar = request.FILES['avatar']
                user.save()
                logger.info("Avatar updated successfully")
            except Exception as e:
                logger.error(f"Failed to save avatar: {str(e)}")
                return Response({"detail": "فشل في حفظ الصورة الشخصية على السيرفر"}, status=400)

        if 'email' in data:
            user.email = data['email']

        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']

        if 'role' in data:
            new_role = data['role']
            if new_role in ['customer', 'agent']:
                user.role = new_role
                if new_role == 'agent' and not hasattr(user, 'agent_profile'):
                    AgentProfile.objects.create(user=user)

        if 'phone_number' in data:
            from .serializers import normalize_iraqi_phone
            phone = normalize_iraqi_phone(data['phone_number'])
            if not phone or not re.match(r'^07[3456789]\d{8}$', phone):
                return Response({"phone_number": ["رقم الهاتف غير صحيح"]}, status=400)
            if user.phone_number.startswith('99') and not phone.startswith('99'):
                user.needs_phone_completion = False
            user.phone_number = phone
            user.username = phone
        elif 'phone' in data:
            user.username = data['phone']

        if 'bio' in data:
            if user.role == 'agent' and hasattr(user, 'agent_profile'):
                user.agent_profile.bio = data['bio']
                user.agent_profile.save(update_fields=['bio'])
            else:
                user.bio = data['bio']

        if user.role == 'agent' and hasattr(user, 'agent_profile'):
            profile = user.agent_profile
            if 'profession' in data:
                profile.profession = data['profession']
            if 'custom_profession' in data:
                profile.custom_profession = data['custom_profession']
            if 'city' in data:
                profile.city = data['city']
            profile.save()

        if 'needs_phone_completion' in data:
            user.needs_phone_completion = data['needs_phone_completion']

        if user.needs_phone_completion and ('role' in data or 'profession' in data):
            user.needs_phone_completion = False

        user.save()

        # إرجاع بيانات المستخدم كاملة باستخدام السيريالايزر مع السياق لضمان روابط الصور الكاملة
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old = request.data.get("old_password")
        new = request.data.get("new_password")
        if not user.check_password(old):
            return Response({"detail": "كلمة المرور القديمة غير صحيحة."}, status=400)
        user.set_password(new)
        user.save()
        return Response({"detail": "تم تغيير كلمة المرور بنجاح."})


class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        logger.info(f"Attempting to delete account for user: {user.phone_number}")

        try:
            # حذف البيانات المرتبطة بحذر (استخدام try/except لكل مجموعة لضمان عدم توقف العملية)
            try:
                RequestAttachment.objects.filter(Q(request__customer=user) | Q(request__agent=user)).delete()
            except: pass

            try:
                RequestTimeline.objects.filter(Q(request__customer=user) | Q(request__agent=user)).delete()
            except: pass

            try:
                Review.objects.filter(Q(customer=user) | Q(agent=user)).delete()
            except: pass

            try:
                RequestMessage.objects.filter(sender=user).delete()
            except: pass

            try:
                WalletTransaction.objects.filter(user=user).delete()
            except: pass

            try:
                Notification.objects.filter(user=user).delete()
            except: pass

            try:
                ServiceRequest.objects.filter(Q(customer=user) | Q(agent=user)).delete()
            except: pass

            try:
                Favorite.objects.filter(user=user).delete()
            except: pass

            if hasattr(user, 'agent_profile'):
                user.agent_profile.delete()
            
            # حذف المستخدم نفسه
            user.delete()
            logger.info(f"User {user.id} deleted successfully")

        except Exception as e:
            logger.exception("Error during account deletion")
            return Response({"detail": f"خطأ أثناء حذف الحساب: {str(e)}"}, status=500)

        return Response({"detail": "تم حذف الحساب بنجاح."})


class AgentProfileView(APIView):
    def put(self, request):
        user = request.user
        if user.role != 'agent':
            return Response({"error": "غير مصرح"}, status=403)
        profile = getattr(user, 'agent_profile', None)
        if not profile:
            return Response({"error": "ملف المهني غير مكتمل"}, status=404)
        data = request.data
        for field in ['bio', 'city', 'profession', 'custom_profession', 'service_min_price', 'service_max_price', 'lat', 'lon']:
            if field in data:
                setattr(profile, field, data[field])
        profile.save()
        return Response({"detail": "تم تحديث ملف المهني"})


class AgentVerificationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        return Response({"detail": "جاري مراجعة طلب توثيق الحساب المهني"})


class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (request.user.is_superuser or request.user.role == 'admin'):
            return Response({"error": "غير مصرح"}, status=403)

        pending_agents = AgentProfile.objects.filter(verification_status='pending').select_related('user')
        data = []
        for agent in pending_agents:
            data.append({
                "id": agent.user.id,
                "name": agent.user.full_name,
                "profession": agent.get_profession_display(),
                "phone": agent.user.phone_number,
                "status": agent.verification_status,
                "id_card_front": agent.id_card_front.url if agent.id_card_front else None,
                "id_card_back": agent.id_card_back.url if agent.id_card_back else None,
            })
        return Response(data, status=200)




class AdminApproveAgentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        if not (request.user.is_superuser or request.user.role == 'admin'):
            return Response({"error": "غير مصرح"}, status=403)

        try:
            user = User.objects.get(id=user_id)
            agent = user.agent_profile
        except (User.DoesNotExist, AgentProfile.DoesNotExist):
            return Response({"error": "المهني غير موجود"}, status=404)

        agent.is_verified = True
        agent.verification_status = 'approved'

        # تحديث اسم المستخدم الرسمي إلى الاسم الذي تم التحقق منه
        if agent.full_name_at_verification:
            names = agent.full_name_at_verification.strip().split()
            if names:
                user.first_name = names[0]
                user.last_name = ' '.join(names[1:]) if len(names) > 1 else ''
                user.save()

        agent.save()

        Notification.objects.create(
            user=agent.user,
            title="✅ تم توثيق حسابك",
            body=f"تم اعتماد حسابك كمهني معتمد في {agent.get_profession_display()}، يمكنك الآن استلام الطلبات.",
            is_active=True
        )

        return Response({"detail": f"تم توثيق المهني {agent.user.full_name} بنجاح"})


class AdminRejectAgentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        if not (request.user.is_superuser or request.user.role == 'admin'):
            return Response({"error": "غير مصرح"}, status=403)

        try:
            user = User.objects.get(id=user_id)
            agent = user.agent_profile
        except (User.DoesNotExist, AgentProfile.DoesNotExist):
            return Response({"error": "المهني غير موجود"}, status=404)

        agent.verification_status = 'rejected'
        agent.is_verified = False
        agent.save()

        Notification.objects.create(
            user=agent.user,
            title="❌ تم رفض طلب التوثيق",
            body="عذراً، لم يتم قبول طلب توثيق حسابك. يرجى التأكد من صحة البطاقة وإعادة المحاولة.",
            is_active=True
        )

        return Response({"detail": f"تم رفض طلب توثيق {agent.user.full_name}"})


class ChangeRoleView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        new_role = request.data.get('role')
        if new_role not in ('customer', 'agent'):
            return Response({"detail": "دور غير صالح"}, status=400)

        user = request.user
        user.role = new_role
        user.save()

        if new_role == 'agent' and not hasattr(user, 'agent_profile'):
            AgentProfile.objects.create(user=user)

        # إرجاع بيانات المستخدم كاملة لضمان تحديث الواجهة والصورة
        serializer = UserSerializer(user, context={'request': request})
        return Response({
            "detail": "تم تغيير نوع الحساب بنجاح",
            "role": new_role,
            "user": serializer.data
        })


class DjangoSessionLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({"error": "Token missing"}, status=400)
        try:
            validated_token = UntypedToken(token)
            user_id = validated_token.get('user_id')
            user = User.objects.get(id=user_id)
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            return Response({"detail": "Session created"})
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": serializer.errors}, status=400)
        serializer.save()
        return Response({"detail": "تم إعادة تعيين كلمة المرور بنجاح."})


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"detail": serializer.errors}, status=400)
        user = serializer.context['user']
        code = f"{random.randint(100000, 999999)}"
        user.reset_code = code
        user.reset_code_expiry = now() + timedelta(minutes=10)
        user.save()
        success, msg = send_sms_via_otpiq(user.phone_number, code)
        if success:
            return Response({"detail": "تم إرسال رمز التحقق إلى هاتفك."})
        else:
            print(f"⚠️ فشل الإرسال: {msg} | الرمز: {code}")
            return Response({"detail": "تم إرسال رمز التحقق (للاختبار، تحقق من وحدة التحكم)."})


# ========== دوال إدارة الصور (صفحات الويب) ==========

def get_or_create_agent_profile(user):
    if user.role != 'agent':
        return None
    profile, created = AgentProfile.objects.get_or_create(user=user)
    if created:
        profile.profession = 'other'
        profile.save()
        messages.add_message(user, messages.INFO, 'تم إنشاء ملفك المهني بنجاح، يمكنك الآن إضافة صور.')
    return profile


@login_required
def add_portfolio_image(request):
    if request.user.role != 'agent':
        messages.error(request, 'هذه الخاصية متاحة فقط لمقدمي الخدمة.')
        return redirect('profileuser')
    profile = get_or_create_agent_profile(request.user)
    if not profile:
        messages.error(request, 'لا يمكن إنشاء الملف المهني.')
        return redirect('profile-mhn')
    if request.method == 'POST':
        form = PortfolioImageForm(request.POST, request.FILES)
        if form.is_valid():
            img = form.save(commit=False)
            img.agent_profile = profile
            img.save()
            messages.success(request, '✅ تمت إضافة الصورة بنجاح!')
            return redirect('profile-mhn')
        else:
            messages.error(request, '❌ فشل رفع الصورة. تأكد من صيغة الملف (jpg/png).')
    else:
        form = PortfolioImageForm()
    return render(request, 'form.html', {'form': form})


@login_required
def delete_portfolio_image(request, pk):
    image = get_object_or_404(PortfolioImage, pk=pk, agent_profile__user=request.user)
    image.delete()
    messages.success(request, '🗑️ تم حذف الصورة بنجاح.')
    return redirect('profile-mhn')


from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

class UploadIdentityView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        user = request.user

        # 1. منع الرفع المتكرر إذا كانت الحالة 'pending' (أمن ومنطق عمل)
        if hasattr(user, 'agent_profile'):
            if user.agent_profile.verification_status == 'pending':
                return Response({"detail": "طلبك قيد المراجعة حالياً، لا يمكنك إعادة الرفع حتى يتم الرد عليك."}, status=status.HTTP_400_BAD_REQUEST)

        if user.role != 'agent':
            logger.warning(f"Access denied for user {user.phone_number}: role is {user.role}")
            return Response({"detail": "يجب أن يكون نوع الحساب 'مندوب' لتتمكن من التوثيق."}, status=status.HTTP_403_FORBIDDEN)

        try:
            # محاولة جلب الملف أو إنشاؤه.
            profile, created = AgentProfile.objects.get_or_create(user=user)

            id_front = request.FILES.get('id_card_front')
            id_back = request.FILES.get('id_card_back')
            whatsapp = request.data.get('whatsapp_number')
            full_name = request.data.get('full_name')

            if not id_front or not id_back:
                return Response({"detail": "يجب رفع وجه البطاقة وظهرها (صور واضحة)"}, status=status.HTTP_400_BAD_REQUEST)

            if not full_name or not whatsapp:
                return Response({"detail": "الاسم الكامل ورقم الواتساب مطلوبان"}, status=status.HTTP_400_BAD_REQUEST)

            # حفظ البيانات
            profile.id_card_front = id_front
            profile.id_card_back = id_back
            profile.whatsapp_number = whatsapp
            profile.full_name_at_verification = full_name
            profile.verification_status = 'pending'
            profile.is_verified = False
            profile.save()

            logger.info(f"Successfully saved identity documents for user {user.phone_number}")

            # إشعار المدير
            try:
                admin_users = User.objects.filter(role='admin')
                for admin in admin_users:
                    Notification.objects.create(
                        user=admin,
                        title="طلب توثيق جديد",
                        body=f"المهني {user.full_name} يطلب توثيق حسابه. قم بمراجعة الوثائق.",
                        is_active=True
                    )
            except Exception as e:
                logger.error(f"Error creating admin notification: {e}")

            return Response({"detail": "✅ تم رفع البطاقة بنجاح. سيتم مراجعتها من قبل الإدارة قريباً."})

        except Exception as e:
            logger.exception(f"Exception during identity upload for user {user.phone_number}")
            return Response({"detail": f"حدث خطأ داخلي أثناء الرفع. يرجى المحاولة لاحقاً."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminAllUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (request.user.is_superuser or request.user.role == 'admin'):
            return Response({"error": "غير مصرح"}, status=403)

        users = User.objects.all().order_by('-date_joined')
        data = []
        for user in users:
            user_data = {
                "id": user.id,
                "name": user.full_name,
                "phone": user.phone_number,
                "role": user.role,
                "is_active": user.is_active,
                "date_joined": user.date_joined.strftime('%Y-%m-%d'),
                "avatar": user.avatar.url if user.avatar else None,
            }
            if user.role == 'agent' and hasattr(user, 'agent_profile'):
                profile = user.agent_profile
                user_data['is_verified'] = profile.is_verified
                user_data['verification_status'] = profile.verification_status
                user_data['id_card_front'] = profile.id_card_front.url if profile.id_card_front else None
                user_data['id_card_back'] = profile.id_card_back.url if profile.id_card_back else None
                user_data['whatsapp_number'] = profile.whatsapp_number
                user_data['full_name_at_verification'] = profile.full_name_at_verification
            else:
                user_data['is_verified'] = None
                user_data['verification_status'] = None
                user_data['id_card_front'] = None
                user_data['id_card_back'] = None
                user_data['whatsapp_number'] = None
                user_data['full_name_at_verification'] = None
            data.append(user_data)
        return Response(data, status=200)
        
        
        
class AdminStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (request.user.is_superuser or request.user.role == 'admin'):
            return Response({"error": "غير مصرح"}, status=403)

        from services.models import ServiceRequest
        from notifications.models import Notification

        total_users = User.objects.count()
        completed_requests = ServiceRequest.objects.filter(status='completed').count()
        pending_requests = ServiceRequest.objects.filter(status='pending').count()
        # تعديل حسب هيكل البلاغات لديك (مثال بسيط)
        new_reports = Notification.objects.filter(is_active=True, title__icontains='بلاغ').count()

        return Response({
            "total_users": total_users,
            "completed_requests": completed_requests,
            "pending_requests": pending_requests,
            "new_reports": new_reports,
        })
        
        
        
        
class FavoriteListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        favs = Favorite.objects.filter(user=request.user).select_related('agent', 'agent__user')
        return Response(FavoriteSerializer(favs, many=True).data)

    def post(self, request):
        agent_id = request.data.get('agent_id')
        agent = get_object_or_404(AgentProfile, id=agent_id)
        fav, created = Favorite.objects.get_or_create(user=request.user, agent=agent)
        if not created:
            return Response({"detail": "موجود مسبقاً في المفضلة"}, status=200)
        return Response(FavoriteSerializer(fav).data, status=201)


class FavoriteDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, agent_id):
        deleted, _ = Favorite.objects.filter(user=request.user, agent_id=agent_id).delete()
        if not deleted:
            return Response({"detail": "غير موجود في المفضلة"}, status=404)
        return Response({"detail": "تمت الإزالة من المفضلة"})


from .serializers import (
    RegisterSerializer, TokenResponseSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    AgentDirectorySerializer, FavoriteSerializer, UserSerializer,
    ProfessionalSerializer, ProfessionalDetailSerializer, CategorySerializer
)
from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class ProfessionalListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        # تصفية المهنيين الموثقين فقط
        queryset = AgentProfile.objects.filter(is_verified=True).select_related('user')

        # استبعاد المستخدم الحالي من القائمة لكي لا يجد نفسه عند البحث
        if request.user.is_authenticated:
            queryset = queryset.exclude(user=request.user)

        category_id = request.query_params.get('category')
        if category_id:
            from services.models import Category
            if category_id.isdigit():
                cat = Category.objects.filter(id=category_id).first()
                if cat and cat.related_profession:
                    queryset = queryset.filter(profession=cat.related_profession)
            else:
                # category_id is a slug/profession value (like 'electrician')
                queryset = queryset.filter(profession=category_id)

        search = request.query_params.get('search')
        if search:
            from services.models import Category

            # تنظيف نص البحث (التطبيع العربي لزيادة دقة النتائج)
            s = search.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ة','ه').replace('ى','ي')

            # جلب المهن المرتبطة بالأقسام التي تطابق نص البحث
            matching_professions = Category.objects.filter(
                Q(name__icontains=search) | Q(name__icontains=s) | Q(description__icontains=search)
            ).values_list('related_profession', flat=True)

            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(bio__icontains=search) |
                Q(custom_profession__icontains=search) |
                Q(profession__in=matching_professions)
            )

        ordering = request.query_params.get('ordering', '-rating')
        if ordering == '-avg_rating':
            ordering = '-rating'
        queryset = queryset.order_by(ordering)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = ProfessionalSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = ProfessionalSerializer(queryset, many=True)
        return Response(serializer.data)

class ProfessionalDetailView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, pk):
        agent = get_object_or_404(AgentProfile, user_id=pk)
        serializer = ProfessionalDetailSerializer(agent)
        return Response(serializer.data)

class CategoryAPIListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        from services.models import Category
        cats = Category.objects.filter(is_active=True)
        return Response(CategorySerializer(cats, many=True).data)

class FeaturedAgentsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        agents = AgentProfile.objects.filter(is_verified=True).select_related('user')

        # استبعاد المستخدم الحالي من قائمة المميزين
        if request.user.is_authenticated:
            agents = agents.exclude(user=request.user)

        agents = agents.order_by('-rating', '-total_jobs')[:10]
        return Response(AgentDirectorySerializer(agents, many=True).data)
