"""
core/urls.py
جدول المسارات الرئيسي — موحّد ومرتّب
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import RedirectView

from . import views
from authentication.views import AdminUserListView, AdminApproveAgentView, AdminRejectAgentView, AdminAllUsersView
from authentication.views import AdminStatsView


def health_check(request):
    return JsonResponse({"status": "ok", "app": "إنجاز", "version": "1.0.0"})


urlpatterns = [
    # ── صفحات عامة ──────────────────────────────────────────────────────────
    path('pricing-guide/', views.pricing_guide, name='pricing-guide'),
    path('favorites/', views.favorites, name='favorites'),
    path('transactions/', views.transactions, name='transactions'),
    path('notifications-page/', views.notifications_page, name='notifications-page'),
    path('faq/', views.faq, name='faq'),
    path('support/', views.support, name='support'),
    path('featured-services/', views.featured_services, name='featured-services'),
    
    # ── صفحات المهني ────────────────────────────────────────────────────────
    path('agent/dashboard/', views.agent_dashboard, name='agent-dashboard'),
    
    # ── صفحات المشرف المخصصة (يجب أن تأتي قبل مسار admin الأصلي) ────────────
    path('admin/dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('admin/users/', views.admin_users, name='admin-users'),
    path('admin/content/', views.admin_content, name='admin-content'),
    path('admin/reports/', views.admin_reports, name='admin-reports'),
    path('admin/analytics/', views.admin_analytics, name='admin-analytics'),
    path('api/admin/stats/', AdminStatsView.as_view(), name='admin-stats'),

    # ── المصادقة ────────────────────────────────────────────────────────────
    path('signin/', views.signin, name='signin'),
    path('register/', views.register, name='register'),
    path('accounts/login/', RedirectView.as_view(url='/signin/', permanent=False), name='login'),
    path('complete-profile/', views.complete_profile, name='complete-profile'),

    # ── البروفايل ───────────────────────────────────────────────────────────
    path('profileuser/', views.profileuser, name='profileuser'),
    path('profile-mhn/', views.profile_mhn, name='profile-mhn'),

    # ── الخدمات والمهن ──────────────────────────────────────────────────────
    path('service-requests/', views.service_requests, name='service-requests'),
    path('profession/<str:profession_slug>/', views.professional_list_view, name='professional_list'),
    path('professional-detail/<int:pk>/', views.professional_detail, name='professional-detail'),
    path('create-request/', views.create_request, name='create-request'),
    path('request-details/', views.request_details, name='request-details'),
    path('request-details/<int:pk>/', views.request_details, name='request-details-pk'),

    # ── المحادثات والمحفظة ──────────────────────────────────────────────────
    path('chat/', views.chat, name='chat'),
    path('wallet-transactions/', views.wallet_transactions, name='wallet-transactions'),

    # ── الإعدادات ───────────────────────────────────────────────────────────
    path('settings/', views.settings_view, name='settings'),

    # ── واجهات الـ API ──────────────────────────────────────────────────────
    path('api/auth/', include('authentication.urls')),
    path('api/services/', include('services.urls')),
    path('api/notifications/', include('notifications.urls')),

    # ── واجهات الـ API الخاصة بالمدير ──────────────────────────────────────
    path('api/admin/users/', AdminUserListView.as_view(), name='admin-users-api'),
    path('api/admin/all-users/', AdminAllUsersView.as_view(), name='admin-all-users'),
    path('api/admin/agents/<int:user_id>/approve/', AdminApproveAgentView.as_view(), name='admin-approve-agent'),
    path('api/admin/agents/<int:user_id>/reject/', AdminRejectAgentView.as_view(), name='admin-reject-agent'),

    # ── أدوات ────────────────────────────────────────────────────────────────
    path('admin/', admin.site.urls),  # Django admin الأصلي (يجب أن يكون في النهاية)
    path('api/healthz', health_check),
    path('api/version', health_check),
    path('sw.js', views.service_worker, name='service-worker'),
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    path('accounts/', include('allauth.urls')),
    
    path('upload-identity/', views.upload_identity_page, name='upload-identity'),

    # ── مسار شات الذكاء الاصطناعي الجديد ────────────────────────────────────
    path('ai-chat/', views.ai_chat_view, name='ai_chat_page'),
]

# خدمة ملفات الميديا والملفات الثابتة
from django.views.static import serve
from django.urls import re_path

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
    ]
