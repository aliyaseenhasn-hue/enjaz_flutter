"""
services/views.py - Minimal Stable Version
"""
import logging
from django.db import transaction
from django.db.models import Q
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
)

from authentication.models import AgentProfile, User
from notifications.models import Notification

logger = logging.getLogger(__name__)

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
                        Notification.objects.create(
                            user=agent,
                            title="طلب خدمة جديد",
                            body=f"لديك طلب خدمة جديد من {request.user.full_name}",
                            request=req
                        )
                except: pass

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
        qs = ServiceRequest.objects.filter(status='pending', agent__isnull=True)
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
    def get(self, request): return Response({"agents": []})

class ChatConversationsView(APIView):
    def get(self, request): return Response([])

class RequestMessagesView(APIView):
    def get(self, request, pk): return Response([])
    def post(self, request, pk): return Response({"message": "ok"})

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
