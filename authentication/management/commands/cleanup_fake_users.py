#!/usr/bin/env python
"""حذف المستخدمين الوهميين - المستخدمين الذين تم إنشاؤهم عبر Google
   بأرقام هواتف وهمية تبدأ بـ 99"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.core.management.base import BaseCommand
from authentication.models import User


class Command(BaseCommand):
    help = 'حذف المستخدمين الوهميين (أرقام تبدأ بـ 99) والذين لم يكملوا رقم الهاتف'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='عرض المستخدمين الذين سيتم حذفهم بدون حذف فعلي',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='حذف جميع المستخدمين الوهميين حتى من لديهم needs_phone_completion=False',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        delete_all = options['all']

        # المستخدمون الوهميون هم من بدأ رقم هاتفهم بـ 99 (تم إنشاؤهم عبر Google)
        fake_users = User.objects.filter(phone_number__startswith='99')
        
        if not delete_all:
            # افتراضياً نحذف فقط من لم يكمل رقم الهاتف
            fake_users = fake_users.filter(needs_phone_completion=True)

        if not fake_users.exists():
            self.stdout.write(self.style.SUCCESS('✅ لا يوجد مستخدمون وهميون للحذف'))
            return

        self.stdout.write(self.style.WARNING(f'⚠️ تم العثور على {fake_users.count()} مستخدم وهمي:'))
        for user in fake_users:
            self.stdout.write(f'  - {user.phone_number} | {user.full_name} | needs_phone: {user.needs_phone_completion}')

        if dry_run:
            self.stdout.write(self.style.WARNING('🧪 وضع المحاكاة - لم يتم حذف أي مستخدم'))
            return

        confirm = input(f'هل تريد حذف {fake_users.count()} مستخدم وهمي؟ (نعم/لا): ')
        if confirm != 'نعم':
            self.stdout.write(self.style.WARNING('❌ تم الإلغاء'))
            return

        # حذف المستخدمين
        deleted_count = 0
        for user in fake_users:
            try:
                # حذف الملفات المرتبطة إن وجدت
                if hasattr(user, 'agent_profile'):
                    user.agent_profile.delete()
                user.delete()
                deleted_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✅ تم حذف {user.phone_number}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ فشل حذف {user.phone_number}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'\n✅ تم حذف {deleted_count} مستخدم وهمي بنجاح'))