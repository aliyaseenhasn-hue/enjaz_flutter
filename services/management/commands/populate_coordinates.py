from django.core.management.base import BaseCommand
from authentication.models import AgentProfile
import random

class Command(BaseCommand):
    help = 'เติมข้อมูลพิกัดภูมิศาสตร์แบบสุ่มให้กับโปรไฟล์ของตัวแทนที่ยังไม่มีข้อมูล'

    def handle(self, *args, **options):
        # พิกัดสำหรับเมืองในอิรัก (สามารถปรับเปลี่ยนได้ตามความเหมาะสม)
        cities_coords = {
            'baghdad': (33.3152, 44.3661),
            'basra': (30.5083, 47.7833),
            'mosul': (36.3451, 43.1391),
            'erbil': (36.1911, 44.0092),
            'sulaymaniyah': (35.5606, 45.4333),
            'kirkuk': (35.4699, 44.3911),
            'najaf': (31.9969, 44.3396),
            'karbala': (32.6167, 44.0333),
        }

        agent_profiles = AgentProfile.objects.filter(lat__isnull=True, lon__isnull=True)
        
        if not agent_profiles.exists():
            self.stdout.write(
                self.style.WARNING('ไม่พบโปรไฟล์ตัวแทนใดๆ ที่ไม่มีข้อมูลพิกัด')
            )
            return
        
        updated_count = 0
        for profile in agent_profiles:
            # สุ่มเลือกเมือง
            city_name, (lat, lon) = random.choice(list(cities_coords.items()))
            
            # เพิ่มค่าสุ่มเล็กน้อยเพื่อให้พิกัดไม่ซ้ำกันทั้งหมด
            lat += random.uniform(-0.1, 0.1)
            lon += random.uniform(-0.1, 0.1)
            
            profile.lat = round(lat, 6)
            profile.lon = round(lon, 6)
            profile.city = city_name.capitalize()
            profile.save(update_fields=['lat', 'lon', 'city'])
            updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'อัปเดตพิกัดเรียบร้อยแล้ว {updated_count} โปรไฟล์ตัวแทน'
            )
        )