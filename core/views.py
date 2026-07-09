"""
core/views.py
دوال عرض الصفحات HTML — متكاملة مع قاعدة البيانات
"""
import requests



import os
import math
from django.conf import settings
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from authentication.models import AgentProfile, User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum


def index(request):
    return redirect('signin')
def upload_identity_page(request):
    return render(request, 'upload-identity.html')

def signin(request):
    return render(request, 'signin.html')


def register(request):
    return render(request, 'signin.html')


def profileuser(request):
    return render(request, 'profileuser.html')


def profile_mhn(request):
    return render(request, 'profile_mhn.html')


def service_requests(request):
    return render(request, 'service-requests.html')

def admin_users(request):
    return render(request, 'admin-users.html')

def admin_content(request):
    return render(request, 'admin-content.html')

def admin_reports(request):
    return render(request, 'admin-reports.html')

def admin_analytics(request):
    return render(request, 'admin-analytics.html')


PROFESSION_TITLES = {
    'electrician':      'أعمال الكهرباء',
    'blacksmith':       'أعمال الحدادة',
    'plumber':          'التأسيسات الصحية',
    'mason':            'أعمال البناء والترميم',
    'painter':          'الدهانات والديكور',
    'carpenter':        'أعمال النجارة',
    'hvac':             'التبريد والتكييف',
    'tile_mason':       'السيراميك والمرمر',
    'developer':        'برمجة وتقنية معلومات',
    'engineer':         'استشارات هندسية',
    'lawyer':           'خدمات قانونية',
    'security_tech':    'الأنظمة الأمنية والكاميرات',
    'clearance_agent':  'معقب معاملات',
    'accountant':       'محاسب',
}

SLUG_TO_PROFESSION = {
    'lawyer':           'lawyer',
    'electrician':      'electrician',
    'plumber':          'plumber',
    'mason':            'mason',
    'painter':          'painter',
    'carpenter':        'carpenter',
    'hvac':             'hvac',
    'tile_mason':       'tile_mason',
    'developer':        'developer',
    'engineer':         'engineer',
    'security_tech':    'security_tech',
    'clearance_agent':  'clearance_agent',
    'accountant':       'accountant',
    'blacksmith':       'other',
}


def _haversine(lat1, lon1, lat2, lon2):
    try:
        r = 6371
        rlat1, rlon1, rlat2, rlon2 = [math.radians(float(x)) for x in [lat1, lon1, lat2, lon2]]
        dlat, dlon = rlat2 - rlat1, rlon2 - rlon1
        a = math.sin(dlat / 2) ** 2 + math.cos(rlat1) * math.cos(rlat2) * math.sin(dlon / 2) ** 2
        return round(r * 2 * math.asin(math.sqrt(a)), 1)
    except (ValueError, TypeError):
        return None


def professional_list_view(request, profession_slug):
    profession_title = PROFESSION_TITLES.get(profession_slug, '')
    prof_value = SLUG_TO_PROFESSION.get(profession_slug, 'other')
    agents = AgentProfile.objects.filter(is_verified=True, profession=prof_value).select_related('user')
    
    user_lat = request.GET.get('lat')
    user_lon = request.GET.get('lon')
    
    professionals = []
    for agent in agents:
        pro_data = {
            'id': agent.user.id,
            'name': agent.user.full_name,
            'avatar': agent.user.avatar.url if agent.user.avatar else None,
            'bio': agent.bio,
            'rating': agent.rating,
            'reviews_count': agent.total_jobs,
            'is_available': True,
            'profession_display': agent.get_profession_display(),
            'city': agent.city,
            'service_min_price': agent.service_min_price,
            'service_max_price': agent.service_max_price,
            'tagline': agent.get_profession_display(),
            'location': agent.city or 'غير محدد',
        }
        
        if user_lat and user_lon and agent.lat and agent.lon:
            try:
                pro_data['distance'] = _haversine(
                    float(user_lat), float(user_lon),
                    float(agent.lat), float(agent.lon)
                )
            except (TypeError, ValueError):
                pro_data['distance'] = None
        else:
            pro_data['distance'] = None
        
        professionals.append(pro_data)
    
    if user_lat and user_lon:
        professionals.sort(key=lambda x: x['distance'] if x['distance'] is not None else 9999)
    
    return render(request, 'professional_list.html', {
        'profession_slug': profession_slug,
        'profession_title': profession_title,
        'professionals': professionals,
        'has_location': bool(user_lat and user_lon),
    })


def professional_detail(request, pk):
    user = get_object_or_404(User, id=pk)
    try:
        agent = user.agent_profile
        if not agent.is_verified:
            return render(request, 'error.html', {'message': 'هذا الملف غير معتمد بعد'}, status=404)
    except AgentProfile.DoesNotExist:
        return render(request, 'error.html', {'message': 'هذا المستخدم ليس مقدماً للخدمات'}, status=404)
    
    user_lat = request.GET.get('lat')
    user_lon = request.GET.get('lon')
    distance = None
    
    if user_lat and user_lon and agent.lat and agent.lon:
        try:
            distance = _haversine(float(user_lat), float(user_lon), float(agent.lat), float(agent.lon))
        except (TypeError, ValueError):
            distance = None
    
    professional_data = {
        'id': user.id,
        'name': user.full_name,
        'avatar': user.avatar.url if user.avatar else None,
        'bio': agent.bio,
        'rating': agent.rating,
        'reviews_count': agent.total_jobs,
        'profession_display': agent.get_profession_display(),
        'city': agent.city or 'غير محدد',
        'distance': distance,
        'service_min_price': agent.service_min_price,
        'service_max_price': agent.service_max_price,
        # ✅ إضافة معرض الأعمال للقالب
        'portfolio_images': agent.portfolio_images.all(),
        # ✅ إضافة رقم الهاتف للتواصل المباشر
        'phone_number': user.phone_number,
        'whatsapp_number': user.phone_number,
    }
    
    return render(request, 'professional_detail.html', {'professional': professional_data})


def create_request(request):
    return render(request, 'create-request.html')


def request_details(request, pk=None):
    return render(request, 'request-details.html', {'request_pk': pk})


def chat(request):
    return render(request, 'chat.html')


def wallet_transactions(request):
    return render(request, 'transactions.html', {'transactions': []})


def settings_view(request):
    return render(request, 'settings.html')


def service_worker(request):
    sw_path = settings.BASE_DIR / 'static' / 'sw.js'
    try:
        return FileResponse(open(sw_path, 'rb'), content_type='application/javascript')
    except FileNotFoundError:
        return HttpResponse('// service worker not found', content_type='application/javascript')


def complete_profile(request):
    return render(request, 'complete-profile.html')


# ══════════════════════════════════════════════════════════
# الصفحات الجديدة (لم تتغير)
# ══════════════════════════════════════════════════════════

def pricing_guide(request):
    """دليل الأسعار الاسترشادية"""
    pricing_data = [
        {'id': 1, 'category': 'كهربائي', 'icon': 'fa-bolt', 'services': [
            {'name': 'تمديد بسيط (3 نقاط)', 'price': '25,000 - 50,000', 'unit': 'د.ع'},
            {'name': 'تمديد متوسط (5-7 نقاط)', 'price': '60,000 - 120,000', 'unit': 'د.ع'},
            {'name': 'تمديد كهربائي كامل', 'price': '150,000 - 300,000', 'unit': 'د.ع'},
            {'name': 'إصلاح فيشة/مفتاح', 'price': '10,000 - 25,000', 'unit': 'د.ع'},
            {'name': 'صيانة لوحة كهربائية', 'price': '30,000 - 80,000', 'unit': 'د.ع'},
        ]},
        {'id': 2, 'category': 'سباك', 'icon': 'fa-faucet-drip', 'services': [
            {'name': 'إصلاح تسريب بسيط', 'price': '15,000 - 35,000', 'unit': 'د.ع'},
            {'name': 'تنظيف مصرف مطبخ', 'price': '20,000 - 40,000', 'unit': 'د.ع'},
            {'name': 'تنظيف مصرف حمام', 'price': '25,000 - 45,000', 'unit': 'د.ع'},
            {'name': 'تركيب خلاط جديد', 'price': '30,000 - 60,000', 'unit': 'د.ع'},
            {'name': 'تغيير أنابيب كاملة', 'price': '100,000 - 250,000', 'unit': 'د.ع'},
        ]},
        {'id': 3, 'category': 'نجار', 'icon': 'fa-hammer', 'services': [
            {'name': 'تصليج باب خشبي', 'price': '20,000 - 50,000', 'unit': 'د.ع'},
            {'name': 'تركيب قفل باب', 'price': '15,000 - 35,000', 'unit': 'د.ع'},
            {'name': 'صنع خزانة ملابس', 'price': '150,000 - 400,000', 'unit': 'د.ع'},
            {'name': 'إصلاح كرسي', 'price': '15,000 - 40,000', 'unit': 'د.ع'},
        ]},
        {'id': 4, 'category': 'دهان', 'icon': 'fa-paint-roller', 'services': [
            {'name': 'دهان غرفة نوم', 'price': '50,000 - 100,000', 'unit': 'د.ع'},
            {'name': 'دهان صالة كاملة', 'price': '80,000 - 150,000', 'unit': 'د.ع'},
            {'name': 'دهان شقة كاملة', 'price': '200,000 - 400,000', 'unit': 'د.ع'},
            {'name': 'دهان خارجي', 'price': '25,000 - 50,000', 'unit': 'م²'},
        ]},
        {'id': 5, 'category': 'تكييف', 'icon': 'fa-snowflake', 'services': [
            {'name': 'صيانة مكيف شباك', 'price': '20,000 - 40,000', 'unit': 'د.ع'},
            {'name': 'صيانة مكيف سبليت', 'price': '30,000 - 60,000', 'unit': 'د.ع'},
            {'name': 'غسيل مكيف', 'price': '15,000 - 35,000', 'unit': 'د.ع'},
            {'name': 'تركيب مكيف', 'price': '50,000 - 100,000', 'unit': 'د.ع'},
        ]},
        {'id': 6, 'category': 'تنظيف', 'icon': 'fa-broom', 'services': [
            {'name': 'تنظيف شقة كاملة', 'price': '40,000 - 80,000', 'unit': 'د.ع'},
            {'name': 'تنظيف مكاتب', 'price': '30,000 - 60,000', 'unit': 'م²'},
            {'name': 'غسيل سجاد', 'price': '5,000 - 10,000', 'unit': 'م²'},
            {'name': 'غسيل خزانات', 'price': '50,000 - 100,000', 'unit': 'د.ع'},
        ]},
        {'id': 7, 'category': 'حدادة', 'icon': 'fa-gears', 'services': [
            {'name': 'صنع بوابة حديد', 'price': '200,000 - 500,000', 'unit': 'د.ع'},
            {'name': 'صنع شبك نافذة', 'price': '30,000 - 80,000', 'unit': 'د.ع'},
            {'name': 'إصلاح باب حديد', 'price': '25,000 - 60,000', 'unit': 'د.ع'},
        ]},
    ]
    return render(request, 'pricing-guide.html', {'pricing_data': pricing_data})


def faq(request):
    """الأسئلة الشائعة"""
    faq_data = [
        {'category': 'تقديم الطلبات', 'icon': 'fa-file-pen', 'questions': [
            {'q': 'كيف أقدم طلب خدمة؟', 'a': 'اضغط على "طلب جديد" في الشريط السفلي، اختر نوع الخدمة، املأ التفاصيل وحدد موقعك.'},
            {'q': 'كم يستغرق الرد على طلبي؟', 'a': 'عادةً خلال 1-3 ساعات، حسب نوع الخدمة وموقعك.'},
            {'q': 'هل يمكنني تعديل طلبي؟', 'a': 'نعم، يمكنك تعديل الطلب قبل قبول أي مهني.'},
        ]},
        {'category': 'الدفع والأسعار', 'icon': 'fa-money-bill-transfer', 'questions': [
            {'q': 'ما هي طرق الدفع؟', 'a': 'الدفع النقدي مباشرة للمهني بعد إتمام العمل.'},
            {'q': 'هل الأسعار نهائية؟', 'a': 'الأسعار استرشادية، يمكنك التفاوض مع المهني.'},
        ]},
        {'category': 'ضمان الجودة', 'icon': 'fa-shield-halved', 'questions': [
            {'q': 'كيف أضمن جودة العمل؟', 'a': 'اقرأ تقييمات العملاء السابقين وشاهد معرض الأعمال.'},
            {'q': 'ماذا أفعل إذا لم أكن راضياً؟', 'a': 'تواصل مع المهني أولاً، وإذا لم يتم الحل قدم بلاغ.'},
        ]},
        {'category': 'المشاكل والبلاغات', 'icon': 'fa-triangle-exclamation', 'questions': [
            {'q': 'كيف أقدم بلاغ؟', 'a': 'اذهب إلى صفحة "الدعم" واختر نوع المشكلة.'},
            {'q': 'متى يتم الرد على البلاغ؟', 'a': 'خلال 24-48 ساعة.'},
        ]},
        {'category': 'حسابي', 'icon': 'fa-user-gear', 'questions': [
            {'q': 'كيف أغير كلمة المرور؟', 'a': 'من الإعدادات > تغيير كلمة المرور.'},
            {'q': 'نسيت كلمة المرور؟', 'a': 'اضغط على "نسيت كلمة المرور" في صفحة الدخول.'},
        ]},
    ]
    return render(request, 'faq.html', {'faq_data': faq_data})


def featured_services(request):
    """الخدمات المميزة"""
    return render(request, 'featured-services.html', {'services': []})


@login_required
def support(request):
    """صفحة الدعم والبلاغات"""
    return render(request, 'support.html')


@login_required
def favorites(request):
    """المهنيين المحفوظين"""
    return render(request, 'favorites.html', {'favorites': []})


@login_required
def transactions(request):
    """سجل المعاملات المالية"""
    return render(request, 'transactions.html', {'transactions': []})


def notifications_page(request):
    """صفحة الإشعارات"""
    return render(request, 'notifications.html', {'notifications': []})


@login_required
def agent_dashboard(request):
    """لوحة تحكم المهني"""
    return render(request, 'agent-dashboard.html', {
        'user': request.user,
        'completed_requests': 0,
        'monthly_earnings': 0,
        'average_rating': 0,
    })


@login_required
def admin_dashboard(request):
    """لوحة تحكم المشرف"""
    return render(request, 'admin-dashboard.html', {
        'total_users': User.objects.count(),
        'completed_requests': 0,
        'pending_requests': 0,
        'new_reports': 0,
        

    })
    
    
    
    
    
    




def ask_ai_view(request):
    # جلب السؤال من الـ Request (مثلاً عبر Query string أو POST)
    user_prompt = request.GET.get("prompt", "مرحبا، كيف حالك؟")

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        # استدعاء المفتاح الذي قمنا بتخزينه في settings.py
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "messages": [{"role": "user", "content": user_prompt}],
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            ai_response = response.json()["choices"][0]["message"]["content"]
            return JsonResponse({"status": "success", "reply": ai_response})
        else:
            return JsonResponse(
                {"status": "error", "message": f"API Error: {response.status_code}"}
            )
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)})


import json
import requests
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# استخدمنا csrf_exempt هنا لتسهيل التجربة من الآيفون وتفادي أخطاء حماية التوكن مؤقتاً
@csrf_exempt
def ai_chat_view(request):  # غيّرنا اسم الدالة هنا لتمييزها
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "")
            
            if not user_message:
                return JsonResponse({"status": "error", "reply": "الرسالة فارغة!"})

            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "messages": [{"role": "user", "content": user_message}],
            }

            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                ai_reply = response.json()["choices"][0]["message"]["content"]
                return JsonResponse({"status": "success", "reply": ai_reply})
            else:
                return JsonResponse({"status": "error", "reply": f"خطأ: {response.status_code}"})

        except Exception as e:
            return JsonResponse({"status": "error", "reply": str(e)})
            
    # استدعاء ملفك الجديد المخصص للذكاء الاصطناعي
    return render(request, "chatai.html")
