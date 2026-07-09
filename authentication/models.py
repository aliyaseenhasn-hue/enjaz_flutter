from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('رقم الهاتف مطلوب')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, role='admin', **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractUser):
    objects = UserManager()
    ROLE_CHOICES = (
        ('customer', 'زبون'),
        ('agent', 'مندوب'),
        ('admin', 'مدير النظام'),
    )

    phone_regex = RegexValidator(
        regex=r'^07[3456789]\d{8}$',
        message="رقم الهاتف يجب أن يكون عراقياً (مثال: 07701234567)"
    )

    phone_number = models.CharField(
        validators=[phone_regex], max_length=15, unique=True,
        verbose_name="رقم الهاتف"
    )
    role = models.CharField(
        max_length=15, choices=ROLE_CHOICES, default='customer',
        verbose_name="نوع الحساب"
    )
    avatar = models.ImageField(
        upload_to='avatars/', null=True, blank=True,
        verbose_name="الصورة الشخصية"
    )
    wallet_balance = models.IntegerField(default=0, verbose_name="رصيد المحفظة")
    username = models.CharField(max_length=150, unique=False, blank=True, null=True)

    # ─── البريد الإلكتروني (اختياري، فريد) ────────────────────────────────
    email = models.EmailField(unique=True, null=True, blank=True, verbose_name="البريد الإلكتروني")

    # ─── حقل يشير إلى أن المستخدم بحاجة لإكمال رقم هاتفه (مثل حسابات Google) ──
    needs_phone_completion = models.BooleanField(default=False, verbose_name="بحاجة لتكملة رقم الهاتف")

    # ─── حقول مؤقتة لتوثيق رقم الهاتف عبر رمز التحقق ──────────────────────
    temp_phone = models.CharField(max_length=15, null=True, blank=True, verbose_name="رقم مؤقت للتحقق")
    verification_code = models.CharField(max_length=10, null=True, blank=True, verbose_name="رمز التحقق")
    verification_code_expiry = models.DateTimeField(null=True, blank=True, verbose_name="انتهاء صلاحية الرمز")

    # ─── حقل توكن الإشعارات (Firebase FCM) ────────────────────────────────
    fcm_token = models.CharField(max_length=255, null=True, blank=True, verbose_name="توكن الإشعارات")

    # ─── حقول إعادة تعيين كلمة المرور ─────────────────────────────────────
    reset_code = models.CharField(max_length=10, null=True, blank=True)
    reset_code_expiry = models.DateTimeField(null=True, blank=True)

    groups = models.ManyToManyField(
        'auth.Group', related_name='enjaz_user_set', blank=True,
        verbose_name='groups'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission', related_name='enjaz_user_permissions_set', blank=True,
        verbose_name='user permissions'
    )

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = "مستخدم"
        verbose_name_plural = "المستخدمون"

    def __str__(self):
        return f"{self.get_role_display()} - {self.phone_number}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class AgentProfile(models.Model):
    STATUS_CHOICES = (
        ('pending', 'قيد المراجعة'),
        ('approved', 'معتمد'),
        ('rejected', 'مرفوض'),
    )
    PROFESSION_CHOICES = (
        ('lawyer', 'محامٍ'),
        ('electrician', 'كهربائي'),
        ('plumber', 'سباك'),
        ('mason', 'بناء'),
        ('painter', 'دهان'),
        ('carpenter', 'نجار'),
        ('hvac', 'فني تبريد وتكييف'),
        ('tile_mason', 'سيراميك'),
        ('developer', 'مبرمج'),
        ('engineer', 'مهندس'),
        ('security_tech', 'فني أنظمة أمنية'),
        ('clearance_agent', 'معقب معاملات'),
        ('accountant', 'محاسب'),
        ('other', 'خدمات أخرى'),
    )
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='agent_profile'
    )
    id_card_front = models.ImageField(
        upload_to='identity/', null=True, blank=True, verbose_name="وجه البطاقة الموحدة"
    )
    id_card_back = models.ImageField(
        upload_to='identity/', null=True, blank=True, verbose_name="ظهر البطاقة الموحدة"
    )
    whatsapp_number = models.CharField(
        max_length=20, blank=True, null=True, verbose_name="رقم الواتساب"
    )
    full_name_at_verification = models.CharField(
        max_length=255, blank=True, null=True, verbose_name="الاسم الكامل عند التوثيق"
    )
    bio = models.TextField(blank=True, verbose_name="نبذة عن المندوب")
    is_verified = models.BooleanField(default=False, verbose_name="موثق")
    verification_status = models.CharField(
        max_length=15, choices=STATUS_CHOICES, default='pending',
        verbose_name="حالة التحقق"
    )
    balance = models.IntegerField(default=0, verbose_name="المحفظة (دينار عراقي)")
    rating = models.FloatField(default=0.0, verbose_name="التقييم")
    total_jobs = models.IntegerField(default=0, verbose_name="إجمالي الأعمال")
    profession = models.CharField(
        max_length=20, choices=PROFESSION_CHOICES, default='other',
        verbose_name="نوع المهنة"
    )
    city = models.CharField(max_length=120, blank=True, verbose_name="المدينة")
    service_min_price = models.PositiveIntegerField(null=True, blank=True, verbose_name="أقل سعر خدمة")
    service_max_price = models.PositiveIntegerField(null=True, blank=True, verbose_name="أعلى سعر خدمة")
    created_at = models.DateTimeField(auto_now_add=True)
    lat = models.DecimalField(max_digits=22, decimal_places=16, null=True, blank=True, verbose_name="خط العرض")
    lon = models.DecimalField(max_digits=22, decimal_places=16, null=True, blank=True, verbose_name="خط الطول")

    custom_profession = models.CharField(max_length=100, blank=True, verbose_name="مهنة أخرى")

    def get_profession_display(self):
        if self.profession == 'other':
            return self.custom_profession if self.custom_profession else "⚠️ لم يحدد المهنة بعد (حدّثها من الإعدادات)"
        return dict(self.PROFESSION_CHOICES).get(self.profession, 'خدمات أخرى')

    class Meta:
        verbose_name = "ملف مندوب"
        verbose_name_plural = "ملفات المندوبين"

    def __str__(self):
        return f"مندوب: {self.user.full_name}"
        
        
class PortfolioImage(models.Model):
    agent_profile = models.ForeignKey('AgentProfile', on_delete=models.CASCADE, related_name='portfolio_images')
    image = models.ImageField(upload_to='portfolio/%Y/%m/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    #class Meta: ordering = ['-uploaded_at']
        
        
        
        
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'agent')
        ordering = ['-created_at']
