#!/usr/bin/env python
"""إصلاح التصنيفات - تعيين related_profession للتصنيفات الموجودة"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.management.base import BaseCommand
from services.models import Category
from authentication.models import AgentProfile


class Command(BaseCommand):
    help = 'إصلاح التصنيفات وتحديث related_profession للتصنيفات الحالية'

    def handle(self, *args, **options):
        # تعيين المهنة المرتبطة لكل تصنيف
        category_mapping = {
            'معاملات حكومية': 'clearance_agent',
            'خدمات المرور وتسجيل السيارات': 'clearance_agent',
            'التوصيل وإنجاز المشاوير': 'other',
            'حجز مواعيد': 'other',
            'خدمات قانونية': 'lawyer',
            'معاملات جوازات': 'clearance_agent',
            'معاملات تقاعد': 'clearance_agent',
            'خدمات بلدية': 'clearance_agent',
            'توصيل مستندات': 'other',
            'كهرباء': 'electrician',
            'سباكة': 'plumber',
            'بناء': 'mason',
            'دهان': 'painter',
            'نجارة': 'carpenter',
            'تبريد وتكييف': 'hvac',
            'سيراميك': 'tile_mason',
            'برمجة وتطوير': 'developer',
            'هندسة': 'engineer',
            'أنظمة أمنية': 'security_tech',
            'محاسبة': 'accountant',
            'خدمات أخرى': 'other',
        }

        updated = 0
        not_found = 0
        
        for cat_name, profession in category_mapping.items():
            cats = Category.objects.filter(name=cat_name)
            if cats.exists():
                for cat in cats:
                    if cat.related_profession != profession:
                        cat.related_profession = profession
                        cat.save(update_fields=['related_profession'])
                        self.stdout.write(f'  ✅ {cat.name} ← {profession}')
                        updated += 1
            else:
                not_found += 1
                self.stdout.write(self.style.WARNING(f'  ⚠️ تصنيف "{cat_name}" غير موجود، تم تخطيه'))

        # عرض التصنيفات التي مازالت بدون related_profession
        unmapped = Category.objects.filter(related_profession__isnull=True)
        if unmapped.exists():
            self.stdout.write(self.style.WARNING(f'\n⚠️ تصنيفات بدون related_profession ({unmapped.count()}):'))
            for cat in unmapped:
                self.stdout.write(f'  - {cat.name} (id={cat.id})')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ تم تحديث {updated} تصنيف'))