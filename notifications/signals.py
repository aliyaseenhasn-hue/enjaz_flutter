from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification
from .utils import send_fcm_notification

@receiver(post_save, sender=Notification)
def push_notification_on_create(sender, instance, created, **kwargs):
    """
    إرسال إشعار دفع (Push Notification) بمجرد إنشاء كائن Notification في قاعدة البيانات
    """
    if created and instance.user.fcm_token:
        data = {}
        if instance.request:
            data['request_id'] = str(instance.request.id)

        send_fcm_notification(
            user=instance.user,
            title=instance.title,
            body=instance.body,
            data=data
        )
