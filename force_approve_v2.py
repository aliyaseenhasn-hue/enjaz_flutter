import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from authentication.models import AgentProfile, User

# تفعيل جميع المهنيين وتعيين بيانات كاملة لضمان ظهورهم في الفلاتر
profiles = AgentProfile.objects.all()
for p in profiles:
    p.is_verified = True
    p.verification_status = 'approved'
    p.city = "بغداد"
    if not p.lat:
        p.lat = 33.3152
        p.lon = 44.3661
    
    # ضمان عدم الاستبعاد بسبب 'other'
    if p.profession == 'other' and not p.custom_profession:
        p.custom_profession = "فني صيانة عامة"
    
    p.save()
    
    user = p.user
    user.role = 'agent'
    user.is_active = True
    user.save()
    print(f"✅ تم تحديث المهني: {user.phone_number} - المهنة: {p.get_profession_display()}")

print("\n🚀 تحديث البيانات اكتمل.")
