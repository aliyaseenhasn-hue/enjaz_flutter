from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification
from .serializers import NotificationSerializer


# notifications/views.py
from .models import Notification
from core.firebase_utils import send_bulk_push_notification

def create_notifications_for_agents(agents, title, body, request_obj=None):
    """إنشاء إشعارات لقائمة من المهنيين (مستخدمين) - bulk_create وإرسال FCM"""
    notifications = []
    for agent in agents:
        notifications.append(
            Notification(
                user=agent,
                title=title,
                body=body,
                request=request_obj,
                is_active=True
            )
        )
    if notifications:
        Notification.objects.bulk_create(notifications)
        # إرسال إشعار Firebase
        tokens = [a.fcm_token for a in agents if a.fcm_token]
        if tokens:
            send_bulk_push_notification(tokens, title, body)


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user,
            is_active=True
        )


class MarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk=None):
        if pk:
            Notification.objects.filter(pk=pk, user=request.user).update(is_read=True)
        else:
            Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"message": "تم تحديث حالة القراءة"})


class UnreadCountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            user=request.user,
            is_read=False,
            is_active=True
        ).count()
        return Response({"unread_count": count})