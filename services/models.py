"""
services/models.py
نماذج قاعدة البيانات للخدمات
"""

from django.conf import settings
from django.db import models
from django.db.models import Avg
from django.db.models.signals import post_save
from django.dispatch import receiver
from authentication.models import AgentProfile


class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="اسم القسم")
    icon = models.CharField(max_length=50, blank=True, verbose_name="أيقونة")
    description = models.TextField(blank=True, verbose_name="وصف القسم")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0, verbose_name="الترتيب")
    related_profession = models.CharField(
        max_length=20,
        choices=AgentProfile.PROFESSION_CHOICES,
        blank=True, null=True,
        verbose_name="المهنة المرتبطة"
    )

    class Meta:
        verbose_name = "تصنيف"
        verbose_name_plural = "التصنيفات"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class ServiceRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'قيد الانتظار'),
        ('in_progress', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    )

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='customer_requests', verbose_name="الزبون"
    )
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='agent_jobs', verbose_name="المهني"
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT, verbose_name="القسم"
    )
    title = models.CharField(max_length=200, verbose_name="عنوان الطلب")
    details = models.TextField(verbose_name="تفاصيل الطلب")
    estimated_price = models.IntegerField(verbose_name="السعر التقديري (د.ع)", null=True, blank=True)
    final_price = models.IntegerField(null=True, blank=True, verbose_name="السعر النهائي (د.ع)")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending',
        verbose_name="حالة الطلب"
    )
    location = models.CharField(max_length=255, blank=True, verbose_name="الموقع")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    lat = models.DecimalField(max_digits=22, decimal_places=16, null=True, blank=True, verbose_name="خط العرض")
    lon = models.DecimalField(max_digits=22, decimal_places=16, null=True, blank=True, verbose_name="خط الطول")

    class Meta:
        verbose_name = "طلب خدمة"
        verbose_name_plural = "طلبات الخدمات"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.get_status_display()}"


class RequestAttachment(models.Model):
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "مرفق"
        verbose_name_plural = "المرفقات"


class RequestTimeline(models.Model):
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='timeline')
    status = models.CharField(max_length=20)
    comment = models.CharField(max_length=500, verbose_name="الحدث")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name='timeline_entries'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "حدث في الجدول الزمني"
        verbose_name_plural = "الجدول الزمني"
        ordering = ['timestamp']


class Review(models.Model):
    REVIEW_TYPES = (
        ('to_agent', 'تقييم للمهني'),
        ('to_customer', 'تقييم للزبون'),
    )
    
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_written',
        null=True, blank=True
    )
    reviewee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews_about_me', null=True, blank=True
    )
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPES, default='to_agent')
    
    rating = models.IntegerField(verbose_name="التقييم (1-5)")
    comment = models.TextField(blank=True, verbose_name="التعليق")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "تقييم"
        verbose_name_plural = "التقييمات"
        unique_together = ('request', 'reviewer', 'review_type')

    def __str__(self):
        return f"تقييم {self.rating}/5 من {self.reviewer} إلى {self.reviewee} ({self.get_review_type_display()})"


class RequestMessage(models.Model):
    request = models.ForeignKey(ServiceRequest, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages'
    )
    content = models.TextField(verbose_name="نص الرسالة")
    is_read = models.BooleanField(default=False, verbose_name="تمت القراءة")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "رسالة طلب"
        verbose_name_plural = "رسائل الطلبات"
        ordering = ['created_at']

    def __str__(self):
        return f"رسالة {self.sender} في {self.request.title}"


class WalletTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'إيداع'),
        ('withdraw', 'سحب'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallet_transactions'
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.IntegerField(verbose_name="المبلغ (د.ع)")
    note = models.CharField(max_length=255, blank=True, verbose_name="ملاحظة")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "معاملة مالية"
        verbose_name_plural = "المعاملات المالية"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()} — {self.amount} د.ع"

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Avg

@receiver(post_save, sender=Review)
def update_user_ratings(sender, instance, **kwargs):
    if instance.review_type == 'to_agent':
        profile = getattr(instance.reviewee, 'agent_profile', None)
        if profile:
            avg = Review.objects.filter(reviewee=instance.reviewee, review_type='to_agent').aggregate(Avg('rating'))['rating__avg']
            profile.rating = avg or 0.0
            profile.save()
    elif instance.review_type == 'to_customer':
        user = instance.reviewee
        avg = Review.objects.filter(reviewee=user, review_type='to_customer').aggregate(Avg('rating'))['rating__avg']
        count = Review.objects.filter(reviewee=user, review_type='to_customer').count()
        user.customer_rating = avg or 0.0
        user.customer_total_reviews = count
        user.save()
