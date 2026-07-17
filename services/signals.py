from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ServiceRequest
from notifications.models import Notification

@receiver(post_save, sender=ServiceRequest)
def notify_agent_on_request_creation(sender, instance, created, **kwargs):
    """
    عند إنشاء طلب جديد موجه لمهني محدد، نقوم بإرسال إشعار فوري له
    """
    if created and instance.agent:
        Notification.objects.create(
            user=instance.agent,
            title="طلب خدمة جديد",
            body=f"لديك طلب جديد من {instance.customer.full_name}: {instance.title}",
            request=instance
        )
