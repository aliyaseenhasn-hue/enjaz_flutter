"""
services/views.py - محسّن مع دعم المهنيين القريبين والموثّقين
"""
import logging
import math
from functools import lru_cache
from django.db import transaction
from django.db.models import Q, Count
from django.core.cache import cache
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404

from .models import (
    Category, RequestAttachment, RequestMessage,
    RequestTimeline, Review, ServiceRequest, WalletTransaction,
)
from .serializers import (
    CategorySerializer, RequestMessageSerializer,
    ReviewSerializer, ServiceRequestDetailSerializer,
    ServiceRequestListSerializer, WalletTransactionSerializer,
    AgentProfileListSerializer, AgentProfileDetailSerializer,
)

from authentication.models import AgentProfile, User
from notifications.models import Notification

logger = logging.getLogger(__name__)


def haversine_distance(lat1, lon1, lat2, lon2):
    """
    تحسب المسافة بالكيلومتر بين نقطتين باستخدام صيغة هافرسين
    """
    R = 6371  # نصف قطر الأرض بالكيلومتر
    try:
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        return round(R * c, 1)
    except (ValueError, TypeError):
        return None

class ServiceRequestCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        logger.info(f"Creating request for user {request.user.phone_number}")
        try:
            with transaction.atomic():
                data = request.data
                category_id = data.get('category_id')
                if not category_id:
                    return Response({"category_id": "هذا الحقل مطلوب"}, status=400)

                # تحويل معرف القسم لرقم بشكل آمن
                try:
                    cat_id = int(category_id)
                    category = Category.objects.get(id=cat_id)
                except (ValueError, TypeError, Category.DoesNotExist):
                    return Response({"category_id": "القسم غير موجود"}, status=404)

                # تنظيف السعر
                est_price = data.get('estimated_price')
                try:
                    if est_price:
                        est_price = int(float(est_price))
                        if est_price <= 0: est_price = None
                except:
                    est_price = None

                # جلب المندوب بشكل آمن
                agent = None
                agent_id = data.get('agent_id') or data.get('professional_id')
                if agent_id:
                    try:
                        agent = User.objects.get(id=int(agent_id))
                    except (ValueError, TypeError, User.DoesNotExist):
                        pass

                # إنشاء الطلب
                req = ServiceRequest.objects.create(
                    customer=request.user,
                    category=category,
                    agent=agent,
                    title=data.get('title', 'طلب خدمة'),
                    details=data.get('details') or data.get('description') or 'بدون تفاصيل',
                    estimated_price=est_price,
                    location=data.get('location', ''),
                    status='pending'
                )

                # حفظ الموقع
                lat = data.get('lat')
                lon = data.get('lon')
                if lat is not None and lon is not None:
                    try:
                        # تحويل آمن للقيم الرقمية
                        if isinstance(lat, str) and not lat.strip():
                            lat = None
                        if isinstance(lon, str) and not lon.strip():
                            lon = None

                        if lat is not None and lon is not None:
                            req.lat = float(lat)
                            req.lon = float(lon)
                            req.save()
                    except (ValueError, TypeError):
                        pass

                # إشعارات
                try:
                    Notification.objects.create(
                        user=request.user,
                        title="تم إنشاء الطلب",
                        body=f"لقد أنشأت طلباً جديداً: {req.title}",
                        request=req
                    )

                    if agent:
                        # طلب مباشر لمهني محدد
                        Notification.objects.create(
                            user=agent,
                            title="طلب خدمة جديد",
                            body=f"لديك طلب خدمة جديد مباشر من {request.user.full_name}",
                            request=req
                        )
                    elif category.related_profession:
                        # طلب عام لكل المهنيين في هذا التخصص
                        target_profession = category.related_profession
                        related_agents = AgentProfile.objects.filter(
                            profession=target_profession,
                            is_verified=True
                        ).exclude(user=request.user).select_related('user')

                        for profile in related_agents:
                            Notification.objects.create(
                                user=profile.user,
                                title=f"طلب جديد في قسم {category.name}",
                                body=f"هناك طلب خدمة جديد متاح: {req.title}",
                                request=req
                            )
                except Exception as e:
                    logger.error(f"Error sending notifications: {e}")

                # إرجاع البيانات بالشكل الذي يتوقعه Flutter (داخل حقل data)
                serializer = ServiceRequestDetailSerializer(req)
                return Response({
                    "message": "تم إنشاء الطلب بنجاح",
                    "id": req.id,
                    "data": serializer.data
                }, status=201)

        except Exception as e:
            logger.exception("ServiceRequestCreateView Critical Error")
            return Response({
                "detail": "Server Error",
                "error": str(e)
            }, status=500)

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

class ServiceRequestDetailView(generics.RetrieveAPIView):
    serializer_class = ServiceRequestDetailSerializer
    queryset = ServiceRequest.objects.all()

class MyRequestsView(generics.ListAPIView):
    serializer_class = ServiceRequestListSerializer
    def get_queryset(self):
        user = self.request.user
        return ServiceRequest.objects.filter(Q(customer=user) | Q(agent=user)).order_by('-created_at')

class AvailableRequestsForAgentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        # استبعاد الطلبات التي أنشأها المستخدم نفسه كزبون
        qs = ServiceRequest.objects.filter(status='pending', agent__isnull=True).exclude(customer=request.user)
        return Response(ServiceRequestListSerializer(qs, many=True).data)

class AcceptRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, pk):
        req = get_object_or_404(ServiceRequest, pk=pk, status='pending')
        req.agent = request.user
        req.status = 'in_progress'
        req.save()
        return Response({"message": "تم القبول"})

class UpdateRequestStatusView(APIView):
    def post(self, request, pk):
        req = get_object_or_404(ServiceRequest, pk=pk)
        req.status = request.data.get('status', req.status)
        req.save()
        return Response({"message": "تم التحديث"})

class CancelRequestView(APIView):
    def post(self, request, pk):
        req = get_object_or_404(ServiceRequest, pk=pk, customer=request.user)
        req.status = 'cancelled'
        req.save()
        return Response({"message": "تم الإلغاء"})

class SubmitReviewView(APIView):
    def post(self, request, pk): return Response({"message": "ok"})

class RejectRequestView(APIView):
    def post(self, request, pk): return Response({"message": "ok"})

class NearbyAgentsView(APIView):
    """
    إرجاع المهنيين الحقيقيين (Verified) مع حساب المسافة بناءً على موقع المستخدم.
    يمكن تمرير ?lat=xxx&lon=xxx&profession=xxx&max_distance=50
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            user_lat = request.query_params.get('lat')
            user_lon = request.query_params.get('lon')
            profession = request.query_params.get('profession')
            max_distance = request.query_params.get('max_distance', 50)

            try:
                max_distance = float(max_distance)
            except (ValueError, TypeError):
                max_distance = 50.0

            # ── استخدام Cache للاستعلامات المتكررة (بدون موقع محدد) ──
            if not user_lat or not user_lon:
                cache_key = f"nearby_agents_{profession or 'all'}"
                cached_data = cache.get(cache_key)
                if cached_data:
                    return Response(cached_data)

            try:
                max_distance = float(max_distance)
            except (ValueError, TypeError):
                max_distance = 50.0

            # جلب المهنيين الحقيقيين فقط (موثقين ومعتمدين)
            # استبعاد المستخدم الحالي إذا كان مهنياً عند البحث عن القريبين
            queryset = AgentProfile.objects.filter(
                is_verified=True,
                verification_status='approved',
                lat__isnull=False,
                lon__isnull=False,
            ).exclude(user=request.user).select_related('user').prefetch_related('portfolio_images')

            # فلترة المتاحين فقط إذا طلب ذلك
            if request.query_params.get('available_now') == 'true':
                queryset = queryset.filter(user__is_online=True)

            if profession:
                queryset = queryset.filter(profession=profession)

            # حساب عدد التقييمات لكل مهني
            queryset = queryset.annotate(reviews_count_cached=Count('user__reviews_received'))

            agents_list = []
            has_location = user_lat and user_lon

            for agent in queryset:
                distance = None
                if has_location:
                    distance = haversine_distance(user_lat, user_lon, agent.lat, agent.lon)

                # فلترة حسب المسافة القصوى
                if has_location and distance is not None and distance > max_distance:
                    continue

                agent_data = AgentProfileListSerializer(agent, context={'request': request}).data
                if has_location:
                    agent_data['distance'] = distance
                else:
                    agent_data['distance'] = None

                agents_list.append(agent_data)

            # ترتيب حسب المسافة إذا كان الموقع متاحاً
            if has_location:
                agents_list.sort(key=lambda x: x.get('distance') or float('inf'))

            return Response({
                'agents': agents_list,
                'total': len(agents_list),
                'has_location': has_location,
            })

        except Exception as e:
            logger.exception("NearbyAgentsView Error")
            return Response({
                'agents': [],
                'total': 0,
                'has_location': False,
                'error': str(e),
            }, status=500)


class AgentDetailView(APIView):
    """
    إرجاع التفاصيل الكاملة لمهني معين مع صور portfolio.
    يمكن تمرير ?lat=xxx&lon=xxx لحساب المسافة.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            # البحث عن المهني (تخفيف القيود للعرض المباشر)
            agent = AgentProfile.objects.filter(pk=pk).select_related('user').prefetch_related('portfolio_images').annotate(
                reviews_count_cached=Count('user__reviews_received')
            ).first()

            if not agent:
                return Response({'error': 'المهني غير موجود'}, status=404)
            
            # إذا لم يكن موثقاً، لا يظهر للآخرين ولكن يظهر لنفسه وللأدمن
            if not agent.is_verified and agent.user != request.user and not request.user.is_superuser:
                return Response({'error': 'هذا الملف بانتظار التوثيق'}, status=403)

            user_lat = request.query_params.get('lat')
            user_lon = request.query_params.get('lon')

            serializer = AgentProfileDetailSerializer(agent, context={'request': request})
            data = serializer.data

            # حساب المسافة إذا كان الموقع متاحاً
            if user_lat and user_lon:
                distance = haversine_distance(user_lat, user_lon, agent.lat, agent.lon)
                data['distance'] = distance
            else:
                data['distance'] = None

            return Response(data)

        except Exception as e:
            logger.exception("AgentDetailView Error")
            return Response({'error': str(e)}, status=500)


class NearbyAgentsByCategoryView(APIView):
    """
    إرجاع المهنيين الحقيقيين حسب القسم (category)
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, category_id):
        try:
            from .models import Category
            category = get_object_or_404(Category, id=category_id)

            # ربط القسم بالمهنة
            profession = category.related_profession
            if not profession:
                # محاولة مطابقة اسم القسم مع كود المهنة من الاختيارات
                for code, label in AgentProfile.PROFESSION_CHOICES:
                    if label in category.name or category.name in label:
                        profession = code
                        break

            if not profession:
                # إذا لم نجد مهنة مطابقة، نبحث عن المهنيين الذين لديهم هذا الاسم في المهنة المخصصة
                request.query_params._mutable = True
                request.query_params['profession'] = category.name
                request.query_params._mutable = False
            else:
                # إعادة توجيه الطلب مع إضافة معلمة المهنة
                request.query_params._mutable = True
                request.query_params['profession'] = profession
                request.query_params._mutable = False

            nearby_view = NearbyAgentsView()
            nearby_view.request = request
            nearby_view.kwargs = {}
            return nearby_view.get(request)

        except Exception as e:
            logger.exception("NearbyAgentsByCategoryView Error")
            return Response({'agents': [], 'total': 0, 'error': str(e)}, status=500)

class ChatConversationsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        user = request.user
        # جلب الطلبات التي يكون المستخدم طرفاً فيها ولديها مهني محدد (لبدء المحادثة)
        requests = ServiceRequest.objects.filter(
            Q(customer=user) | Q(agent=user)
        ).filter(agent__isnull=False).order_by('-updated_at')

        return Response(ServiceRequestListSerializer(requests, many=True).data)

class RequestMessagesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        req = get_object_or_404(ServiceRequest, pk=pk)
        if request.user != req.customer and request.user != req.agent:
            return Response({"detail": "غير مصرح لك"}, status=403)

        messages = req.messages.all().order_by('created_at')
        return Response(RequestMessageSerializer(messages, many=True).data)

    def post(self, request, pk):
        req = get_object_or_404(ServiceRequest, pk=pk)
        if request.user != req.customer and request.user != req.agent:
            return Response({"detail": "غير مصرح لك"}, status=403)

        content = request.data.get('content')
        if not content:
            return Response({"content": "الرسالة فارغة"}, status=400)

        msg = RequestMessage.objects.create(
            request=req,
            sender=request.user,
            content=content
        )

        # إشعار للطرف الآخر
        other_user = req.agent if request.user == req.customer else req.customer
        if other_user:
            try:
                Notification.objects.create(
                    user=other_user,
                    title=f"رسالة جديدة من {request.user.full_name}",
                    body=content[:50] + "..." if len(content) > 50 else content,
                    request=req
                )
            except: pass

        return Response(RequestMessageSerializer(msg).data, status=201)

class WalletInfoView(APIView):
    def get(self, request): return Response({'balance': 0})

class WalletTransactionsView(generics.ListAPIView):
    serializer_class = WalletTransactionSerializer
    def get_queryset(self): return WalletTransaction.objects.filter(user=self.request.user)

class WalletDepositView(APIView):
    def post(self, request): return Response({"message": "ok"})

class WalletWithdrawView(APIView):
    def post(self, request): return Response({"message": "ok"})

class AdminRequestListView(generics.ListAPIView):
    serializer_class = ServiceRequestListSerializer
    queryset = ServiceRequest.objects.all()

class AdminAssignAgentView(APIView):
    def post(self, request, pk): return Response({"message": "ok"})

class AdminStatsView(APIView):
    def get(self, request): return Response({"total": 0})
