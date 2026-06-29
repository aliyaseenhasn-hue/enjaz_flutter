# ProLink - Claude Project Memory

## نظرة عامة
منصة تربط المهنيين بطالبي الخدمة، مشابهة لـ Uber للخدمات المنزلية والمهنية.
مستهدفة العراق، عربي RTL.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2 + DRF |
| Auth | JWT (SimpleJWT) + OTP هاتف |
| Database | PostgreSQL |
| Real-time | Django Channels + Redis (WebSocket) |
| Storage | Cloudinary |
| Push | Firebase FCM |
| Task Queue | Celery + Redis |
| Frontend Mobile | Flutter |
| State | Riverpod |
| Navigation | GoRouter |
| HTTP | Dio + JWT auto-refresh |
| Deploy | Railway (railway.toml + Procfile) |

---

## هيكل Backend `/home/claude/prolink/`

```
core/
  settings.py       ← إعدادات كاملة
  urls.py           ← روابط رئيسية
  asgi.py           ← WebSocket setup
  admin.py          ← Admin panel كامل

users/
  models.py         ← User custom + OTPCode
  serializers.py    ← Register, Login, Profile, Identity
  views.py          ← register, verify_otp, login, logout, profile
  urls.py

professionals/
  models.py         ← Category, Skill, ProfessionalProfile, Portfolio, WorkingHours
  serializers.py
  views.py          ← list, detail, nearby (Haversine), availability
  urls.py
  management/commands/seed_data.py ← 10 تصنيفات جاهزة

requests/
  models.py         ← ServiceRequest, PriceOffer, RequestImage
  serializers.py
  views.py          ← CRUD + accept/reject/cancel/complete + negotiation
  urls.py

chat/
  models.py         ← Conversation, Message
  consumers.py      ← WebSocket consumer (JWT auth)
  routing.py
  serializers.py
  views.py
  urls.py

reviews/
  models.py         ← Review (يحدث avg_rating تلقائياً)
  views.py

notifications/
  models.py         ← Notification
  utils.py          ← send_notification() → DB + Firebase
  views.py

requirements.txt
.env.example
Procfile
railway.toml
API_DOCS.md
```

---

## هيكل Flutter `/home/claude/prolink_flutter/`

```
lib/
  core/
    constants/app_constants.dart   ← BASE_URL, WS_URL, keys
    theme/app_theme.dart           ← AppColors + ThemeData كامل
    utils/
      api_client.dart              ← Dio + JWT interceptor + auto-refresh
      app_router.dart              ← GoRouter كامل
      auth_state.dart              ← AuthNotifier + AuthState

  features/
    auth/
      data/
        models/user_model.dart
        repositories/auth_repository.dart
      presentation/screens/
        splash_screen.dart
        login_screen.dart
        register_screen.dart       ← role selection cards
        otp_screen.dart            ← 6-box OTP + countdown
        identity_verification_screen.dart

    home/
      presentation/screens/main_screen.dart  ← NavigationBar shell

    professionals/
      data/
        models/professional_model.dart
        repositories/professionals_repository.dart ← filter provider
      presentation/screens/
        professional_list_screen.dart   ← search + categories + filters
        professional_detail_screen.dart ← hero image + portfolio

    requests/
      data/models/request_model.dart   ← ServiceRequest + PriceOffer
      presentation/screens/
        requests_list_screen.dart      ← TabBar (الكل/انتظار/جارية/مكتملة)
        create_request_screen.dart     ← form + urgent toggle
        request_detail_screen.dart     ← negotiation bubbles + actions

    chat/
      data/models/chat_model.dart
      presentation/screens/
        chat_list_screen.dart
        chat_screen.dart               ← WebSocket حقيقي

    notifications/
      presentation/screens/notifications_screen.dart

    profile/
      presentation/screens/profile_screen.dart

pubspec.yaml
```

---

## API Endpoints ملخص

```
POST /api/auth/register/
POST /api/auth/verify-otp/
POST /api/auth/login/
POST /api/auth/logout/
GET/PUT /api/auth/profile/
PUT /api/auth/profile/identity/

GET /api/professionals/categories/
GET /api/professionals/               ← ?category=&city=&min_rating=&available_now=
GET /api/professionals/nearby/        ← ?lat=&lng=&radius=
GET /api/professionals/<uuid>/
GET/PUT /api/professionals/me/
POST /api/professionals/me/availability/

GET /api/requests/
POST /api/requests/create/
GET /api/requests/<uuid>/
POST /api/requests/<uuid>/accept/
POST /api/requests/<uuid>/reject/
POST /api/requests/<uuid>/cancel/
POST /api/requests/<uuid>/complete/
POST /api/requests/<uuid>/offer/
POST /api/requests/<uuid>/offer/<id>/accept/

GET /api/chat/
POST /api/chat/start/
GET /api/chat/<uuid>/messages/
WS  wss://domain/ws/chat/<uuid>/?token=<jwt>

GET /api/reviews/professional/<uuid>/
POST /api/reviews/create/

GET /api/notifications/
POST /api/notifications/read-all/
POST /api/notifications/<uuid>/read/
```

---

## متغيرات البيئة المطلوبة (.env)

```env
SECRET_KEY=
DEBUG=False
ALLOWED_HOSTS=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=5432
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
REDIS_URL=redis://localhost:6379
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
CORS_ORIGINS=
```

---

## خطوات التشغيل

```bash
# Backend
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data      # يضيف 10 تصنيفات
python manage.py createsuperuser
daphne core.asgi:application    # أو: python manage.py runserver

# Flutter
flutter pub get
flutter run
```

---

## ما تبقى للإكمال

### Flutter (لم يُبنى بعد)
- [ ] `edit_profile_screen.dart` ← تعديل الاسم/البيو/المدينة + رفع صورة
- [ ] `add_review_screen.dart` ← star rating + تعليق
- [ ] Professional me screen ← إدارة الملف المهني للمهني
- [ ] `main.dart` ← نقطة الدخول مع Riverpod + GoRouter + Theme + Localizations
- [ ] `AndroidManifest.xml` ← permissions (INTERNET, CAMERA, LOCATION)
- [ ] `google-services.json` ← Firebase config
- [ ] Font files في `assets/fonts/` (Cairo)

### Backend (اختياري للإكمال)
- [ ] SMS provider حقيقي (Twilio / OTPIQ)
- [ ] Celery tasks للإشعارات المجدولة
- [ ] `manage.py wsgi.py` ← تأكد من وجوده

---

## ملاحظات مهمة

- **Auth Flow:** register → OTP verify → (identity upload اختياري) → home
- **WebSocket URL:** يحتاج `?token=<access_jwt>` في query string
- **Price Negotiation:** كلا الطرفين يرسل عروضاً، أي طرف يقبل = confirmed
- **Haversine:** في `professionals/views.py` → `nearby_professionals()`
- **Admin approval:** `is_identity_verified` يُفعَّل من Admin panel
- **AppColors.primary = #2563EB** (أزرق)، **secondary = #10B981** (أخضر)
- **Font:** Cairo (عربي) - يجب رفع ملفات TTF إلى `assets/fonts/`
- **Base URL:** غيّر `AppConstants.baseUrl` في `app_constants.dart`
