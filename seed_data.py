#!/usr/bin/env python
"""بيانات تجريبية لمشروع إنجاز"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from authentication.models import User, AgentProfile
from services.models import Category, ServiceRequest, RequestTimeline
from notifications.models import Notification


def seed():
    print("🌱 بدء إدراج البيانات التجريبية...")

    categories_data = [
        {"name": "معاملات حكومية", "icon": "🏛️", "order": 1, "related_profession": "clearance_agent"},
        {"name": "خدمات المرور وتسجيل السيارات", "icon": "🚗", "order": 2, "related_profession": "clearance_agent"},
        {"name": "التوصيل وإنجاز المشاوير", "icon": "🛵", "order": 3, "related_profession": "other"},
        {"name": "حجز مواعيد", "icon": "📅", "order": 4, "related_profession": "other"},
        {"name": "خدمات قانونية", "icon": "⚖️", "order": 5, "related_profession": "lawyer"},
        {"name": "معاملات جوازات", "icon": "🛂", "order": 6, "related_profession": "clearance_agent"},
        {"name": "معاملات تقاعد", "icon": "👴", "order": 7, "related_profession": "clearance_agent"},
        {"name": "خدمات بلدية", "icon": "🏙️", "order": 8, "related_profession": "clearance_agent"},
        {"name": "توصيل مستندات", "icon": "📄", "order": 9, "related_profession": "other"},
    ]
    for cat in categories_data:
        Category.objects.get_or_create(name=cat["name"], defaults=cat)
    print(f"  ✅ أُنشئت {len(categories_data)} تصنيفات")

    if not User.objects.filter(phone_number='07700000001').exists():
        admin = User.objects.create_superuser(
            phone_number='07700000001',
            password='admin123456',
            first_name='مدير',
            last_name='النظام',
            role='admin',
        )
        print(f"  ✅ أُنشئ حساب المدير: {admin.phone_number}")

    customers = [
        {'phone_number': '07701111001', 'first_name': 'أحمد', 'last_name': 'الكاظمي', 'role': 'customer'},
        {'phone_number': '07701111002', 'first_name': 'سارة', 'last_name': 'العبيدي', 'role': 'customer'},
        {'phone_number': '07701111003', 'first_name': 'محمد', 'last_name': 'الجبوري', 'role': 'customer'},
    ]
    for c in customers:
        if not User.objects.filter(phone_number=c['phone_number']).exists():
            User.objects.create_user(password='test123456', **c)
    print(f"  ✅ أُنشئ {len(customers)} عملاء")

    agents_data = [
        {'phone_number': '07702222001', 'first_name': 'علي', 'last_name': 'الحسني', 'role': 'agent'},
        {'phone_number': '07702222002', 'first_name': 'زينب', 'last_name': 'الموسوي', 'role': 'agent'},
    ]
    for a in agents_data:
        if not User.objects.filter(phone_number=a['phone_number']).exists():
            agent_user = User.objects.create_user(password='test123456', **a)
            AgentProfile.objects.create(
                user=agent_user,
                id_card_front='identity/sample.jpg',
                id_card_back='identity/sample.jpg',
                bio='مندوب معتمد متخصص في المعاملات الحكومية',
                is_verified=True,
                verification_status='approved',
                balance=50000,
                rating=4.5,
                total_jobs=12,
            )
    print(f"  ✅ أُنشئ {len(agents_data)} مندوبين")

    cat_gov = Category.objects.get(name='معاملات حكومية')
    cat_car = Category.objects.get(name='خدمات المرور وتسجيل السيارات')
    customer1 = User.objects.get(phone_number='07701111001')
    customer2 = User.objects.get(phone_number='07701111002')
    agent1 = User.objects.get(phone_number='07702222001')

    requests_data = [
        {
            'customer': customer1,
            'category': cat_gov,
            'title': 'استخراج شهادة الجنسية',
            'details': 'أحتاج استخراج شهادة جنسية من دائرة الجنسية في الكرادة',
            'estimated_price': 25000,
            'status': 'completed',
            'agent': agent1,
        },
        {
            'customer': customer2,
            'category': cat_car,
            'title': 'تجديد لوحة السيارة',
            'details': 'تجديد لوحة سيارة تويوتا كامري موديل 2018',
            'estimated_price': 15000,
            'status': 'pending',
        },
        {
            'customer': customer1,
            'category': cat_gov,
            'title': 'معاملة الهوية الوطنية',
            'details': 'تجديد الهوية الوطنية المنتهية الصلاحية',
            'estimated_price': 20000,
            'status': 'in_progress',
            'agent': agent1,
        },
    ]
    for r in requests_data:
        req, created = ServiceRequest.objects.get_or_create(
            customer=r['customer'],
            title=r['title'],
            defaults=r
        )
        if created:
            RequestTimeline.objects.create(
                request=req,
                status=r['status'],
                comment='تم إنشاء الطلب',
                created_by=r['customer']
            )
    print(f"  ✅ أُنشئت {len(requests_data)} طلبات تجريبية")

    print("\n✅ اكتملت البيانات التجريبية بنجاح!")
    print("\n📋 بيانات الدخول:")
    print("  المدير:   07700000001 / admin123456")
    print("  عميل 1:   07701111001 / test123456")
    print("  عميل 2:   07701111002 / test123456")
    print("  مندوب 1:  07702222001 / test123456")
    print("  مندوب 2:  07702222002 / test123456")


if __name__ == '__main__':
    seed()
