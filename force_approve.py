import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from authentication.models import AgentProfile, User

# تفعيل جميع المهنيين وتعيين موقع افتراضي في بغداد لغرض التجربة
profiles = AgentProfile.objects.all()
for p in profiles:
    p.is_verified = True
    p.verification_status = 'approved'
    if not p.lat:
        p.lat = 33.3152
        p.lon = 44.3661
    p.save()
    
    # التأكد من أن الدور هو مهني
    user = p.user
    user.role = 'agent'
    user.save()
    print(f"✅ الحساب {user.phone_number} أصبح الآن مهنياً مفعل وموجود في بغداد.")

print("\n🚀 جميع الحسابات جاهزة الآن للظهور في نتائج البحث.")
