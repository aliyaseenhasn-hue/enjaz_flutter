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
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
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
            if not phone:
                return Response({"detail": "رقم الهاتف غير صالح."}, status=400)

            logger.info(f"Attempting login for phone: {phone}")
            
            # استخدام الحقل المخصص phone_number للمصادقة
            try:
                # محاولة جلب المستخدم مباشرة حسب رقم الهاتف
                user = User.objects.get(phone_number=phone)
                
                # التحقق من كلمة المرور
                if user.check_password(password):
                    if not user.is_active: 
                        return Response({"detail": "هذا الحساب معطل."}, status=400)
                    
                    refresh = RefreshToken.for_user(user)
                    return Response({
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                        "role": getattr(user, 'role', 'customer'),
                        "user": UserSerializer(user, context={'request': request}).data,
                        "detail": "تم تسجيل الدخول بنجاح."
                    }, status=200)
                else:
                    return Response({"detail": "رقم الهاتف أو كلمة المرور غير صحيحة."}, status=401)
            except User.DoesNotExist:
                return Response({"detail": "رقم الهاتف أو كلمة المرور غير صحيحة."}, status=401)
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
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

@api_view(['GET'])
@permission_classes([AllowAny])
def test_connection(request):
    return Response({
        "status": "connected",
        "message": "تم الاتصال بالسيرفر بنجاح!",
        "database": "online"
    })

class SendVerificationCodeView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        try:
            phone_raw = request.data.get('phone_number')
            if not phone_raw:
                return Response({"detail": "يرجى إدخال رقم الهاتف"}, status=400)
            
            phone = internal_normalize_phone(phone_raw)
            if not phone:
                return Response({"detail": "رقم الهاتف غير صالح"}, status=400)

            # إنشاء رمز افتراضي للتطوير
            otp = "123456"

            # حفظ الرمز في قاعدة البيانات للمستخدم (إن وجد) أو بشكل مؤقت
            # استخدام update_or_create لتجنب مشكلة username المطلوب
            user, created = User.objects.get_or_create(
                phone_number=phone,
                defaults={
                    'username': phone,
                    'first_name': phone,
                    'last_name': '',
                }
            )
            user.verification_code = otp
            user.verification_code_expiry = now() + timedelta(minutes=10)
            user.save()

            return Response({
                "detail": f"تم إرسال رمز التحقق إلى {phone_raw}",
                "debug_otp": otp # للسهولة أثناء التطوير
            }, status=200)
        except Exception as e:
            logger.error(f"Error sending verification code: {str(e)}", exc_info=True)
            return Response({
                "detail": "حدث خطأ أثناء إرسال رمز التحقق",
                "error": str(e),
                "traceback": traceback.format_exc()
            }, status=500)

class VerifyPhoneView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        phone_raw = request.data.get('phone_number')
        code = request.data.get('code')
        
        if not phone_raw or not code:
            return Response({"detail": "البيانات ناقصة"}, status=400)
            
        phone = internal_normalize_phone(phone_raw)
        try:
            user = User.objects.get(phone_number=phone)
            
            # التحقق من الرمز (دعم الرمز الافتراضي 123456 للتطوير)
            is_valid = (str(user.verification_code) == str(code)) or (str(code) == "123456")

            if is_valid:
                # التحقق من الصلاحية (إلا إذا كان الرمز هو الافتراضي)
                if str(code) != "123456":
                    if user.verification_code_expiry and user.verification_code_expiry < now():
                        return Response({"detail": "انتهت صلاحية الرمز"}, status=400)
                
                # تفعيل الحساب
                user.is_active = True
                user.is_customer_verified = True
                user.verification_code = "" # مسح الرمز بعد الاستخدام
                user.save()
                
                # توليد التوكن
                refresh = RefreshToken.for_user(user)
                return Response({
                    "access": str(refresh.access_token),
                    "refresh": str(refresh),
                    "is_profile_complete": user.is_profile_complete,
                    "user": UserSerializer(user, context={'request': request}).data,
                    "detail": "تم التحقق بنجاح"
                }, status=200)
            else:
                return Response({"detail": "رمز التحقق غير صحيح"}, status=400)
                
        except User.DoesNotExist:
            return Response({"detail": "لم يتم إرسال رمز لهذا الرقم"}, status=404)

class CompleteProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        user = request.user
        full_name = request.data.get('full_name')
        role = request.data.get('role', 'customer')
        avatar = request.FILES.get('avatar')
        
        if not full_name:
            return Response({"detail": "الاسم الكامل مطلوب"}, status=400)
            
        # تقسيم الاسم
        names = full_name.split(' ')
        user.first_name = names[0]
        user.last_name = " ".join(names[1:]) if len(names) > 1 else ""
        
        if role in ['customer', 'agent']:
            user.role = role
            
        if avatar:
            user.avatar = avatar
            
        user.is_profile_complete = True
        user.save()
        
        # إنشاء بروفايل مهني إذا اختار دور مهني
        if role == 'agent':
            AgentProfile.objects.get_or_create(user=user)
            
        return Response({
            "detail": "تم إكمال الملف الشخصي بنجاح",
            "user": UserSerializer(user, context={'request': request}).data
        }, status=200)

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
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    def get(self, request): return Response(UserSerializer(request.user, context={'request': request}).data)
    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            # تحديث الكائن من قاعدة البيانات لضمان شمول تغييرات الـ AgentProfile
            request.user.refresh_from_db()
            return Response(UserSerializer(request.user, context={'request': request}).data)
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
        try:
            profile, _ = AgentProfile.objects.get_or_create(user=request.user)
            # تحديث البيانات يدوياً لضمان الدقة (أو عبر السيريالايزر)
            profession = request.data.get('profession')
            custom_profession = request.data.get('custom_profession')
            city = request.data.get('city')
            whatsapp = request.data.get('whatsapp_number')
            bio = request.data.get('bio')
            lat = request.data.get('lat')
            lon = request.data.get('lon') or request.data.get('lng')

            if profession: profile.profession = profession
            if custom_profession is not None: profile.custom_profession = custom_profession
            if city: profile.city = city
            if whatsapp: profile.whatsapp_number = whatsapp
            if bio: profile.bio = bio
            if lat: profile.lat = lat
            if lon: profile.lon = lon

            profile.save()
            
            # 🔥 مسح العلاقة المخبأة في request.user (cached agent_profile)
            # حتى يعيد جلبها من قاعدة البيانات في الطلب التالي
            try:
                del request.user.agent_profile
            except (AttributeError, KeyError):
                pass
            
            return Response(AgentProfileSerializer(profile, context={'request': request}).data)
        except Exception as e:
            return Response({"detail": str(e)}, status=400)

    def get(self, request):
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
        if role not in ['customer', 'agent']:
            return Response({"detail": "دور غير صالح"}, status=400)
        
        if request.user.role == role:
            return Response({"detail": "أنت بالفعل في هذا الدور"})

        # منع التبديل عند وجود طلبات نشطة
        from services.models import ServiceRequest
        active_statuses = ['pending', 'in_progress', 'negotiating', 'confirmed']
        
        # التحقق من وجود طلبات نشطة للمستخدم كزبون أو كمهني
        has_active = ServiceRequest.objects.filter(
            Q(customer=request.user) | Q(agent=request.user),
            status__in=active_statuses
        ).exists()
        
        if has_active:
            return Response({
                "detail": "لا يمكنك تغيير نوع الحساب أثناء وجود طلبات جارية. يرجى إكمال مهامك أو إلغاؤها أولاً."
            }, status=400)

        # التحقق من الحظر العام للمستخدم
        if getattr(request.user, 'is_blacklisted', False):
            return Response({"detail": "هذا الحساب محظور من تغيير الأدوار."}, status=403)

        # تغيير الدور وحفظه
        request.user.role = role
        request.user.save()
        
        return Response({
            "detail": f"تم تحويل حسابك إلى وضع {request.user.get_role_display()} بنجاح",
            "role": role,
            "user": UserSerializer(request.user, context={'request': request}).data
        })

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
        # تصفية المهنيين الحقيقيين فقط والموثقين
        # جعلنا حالة is_online اختيارية لتسهيل ظهور المهنيين المسجلين
        agents = AgentProfile.objects.filter(
            is_verified=True
        )

        # اختيارياً: التصفية حسب المتاحين فقط إذا تم تمرير المعامل
        # أو إذا كانت فئة المحاماة لضمان جلب النشطين والقريبين
        if request.query_params.get('available_now') == 'true':
            agents = agents.filter(user__is_online=True)

        # استبعاد المهنيين الذين لم يحددوا تخصصهم بعد
        agents = agents.exclude(
            profession='other', custom_profession=''
        ).exclude(
            profession='other', custom_profession__isnull=True
        )

        # منطق البحث عن القريبين إذا تم إرسال lat و lng
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius = request.query_params.get('radius', 50) # النطاق الافتراضي 50 كم
        category = request.query_params.get('category')

        if category:
            from services.models import Category
            try:
                # محاولة البحث إذا كان المرسل هو ID القسم
                cat_obj = Category.objects.get(id=int(category))

                if cat_obj.related_profession:
                    # تصفية حسب المهنة المرتبطة بالقسم
                    agents = agents.filter(profession=cat_obj.related_profession)
                else:
                    # محاولة مطابقة اسم القسم مع كود المهنة من الاختيارات
                    profession_code = None
                    for code, label in AgentProfile.PROFESSION_CHOICES:
                        if label in cat_obj.name or cat_obj.name in label:
                            profession_code = code
                            break

                    if profession_code:
                        agents = agents.filter(profession=profession_code)
                    else:
                        agents = agents.filter(
                            Q(profession__icontains=cat_obj.name) |
                            Q(custom_profession__icontains=cat_obj.name)
                        )
            except (ValueError, Category.DoesNotExist):
                # إذا لم يكن رقماً، نفترض أنه نص المهنة مباشرة
                agents = agents.filter(Q(profession=category) | Q(custom_profession__icontains=category))

        # دعم معلمات الموقع بكلا الاسمين lng و lon
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng') or request.query_params.get('lon')
        radius = request.query_params.get('radius', 50)

        if lat and lng:
            try:
                user_lat = float(lat)
                user_lng = float(lng)
                radius_km = float(radius)
                
                # فلترة المربع (Bounding Box) لتسريع الأداء
                lat_deg = radius_km / 111.0
                lng_deg = radius_km / (111.0 * 0.8) 

                agents = agents.filter(
                    lat__gte=user_lat - lat_deg,
                    lat__lte=user_lat + lat_deg,
                    lon__gte=user_lng - lng_deg,
                    lon__lte=user_lng + lng_deg
                )
            except (TypeError, ValueError):
                pass
        
        # دعم الترتيب
        ordering = request.query_params.get('ordering', '-rating')
        if 'avg_rating' in ordering:
            ordering = ordering.replace('avg_rating', 'rating')
        
        try:
            agents = agents.order_by(ordering)
        except:
            agents = agents.order_by('-rating')

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

class AddPortfolioImageView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        """إضافة صورة إلى معرض المندوب"""
        try:
            if not request.user.is_authenticated:
                return Response({"detail": "يجب تسجيل الدخول أولاً"}, status=401)
            
            # الحصول على AgentProfile
            profile = getattr(request.user, 'agent_profile', None)
            if not profile:
                profile, created = AgentProfile.objects.get_or_create(user=request.user)
            
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
                "portfolio": PortfolioItemSerializer(portfolio_img, context={'request': request}).data
            }, status=201)
        except Exception as e:
            logger.error(f"Error adding portfolio image: {str(e)}")
            return Response({"detail": f"حدث خطأ: {str(e)}"}, status=500)

class DeletePortfolioImageView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, pk):
        """حذف صورة من معرض المندوب"""
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