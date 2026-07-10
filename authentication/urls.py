from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views


urlpatterns = [
    # ── المصادقة الأساسية ────────────────────────────────────────────────
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),

    # ── تسجيل الدخول عبر Google (يجب أن يكون قبل مسارات dj_rest_auth) ──
    path('google/', views.GoogleAuthView.as_view(), name='google-auth'),

    # ── تحديث الملف الشخصي والحساب ───────────────────────────────────────
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('profile/delete/', views.DeleteAccountView.as_view(), name='delete-account'),

    # ── توثيق رقم الهاتف وتعيين كلمة المرور (لحسابات Google) ────────────
    path('send-verification-code/', views.SendVerificationCodeView.as_view(), name='send-verification-code'),
    path('verify-phone/', views.VerifyPhoneView.as_view(), name='verify-phone'),
    path('toggle-online/', views.ToggleOnlineView.as_view(), name='toggle-online'),
    path('update-fcm-token/', views.UpdateFcmTokenView.as_view(), name='update-fcm-token'),

    # ── إدارة المهنيين ──────────────────────────────────────────────────
    path('agent/profile/', views.AgentProfileView.as_view(), name='agent-profile'),
    path('agent/verify/', views.AgentVerificationView.as_view(), name='agent-verify'),

    # ── إدارة المشرف (Admin) ────────────────────────────────────────────
    path('admin/users/all/', views.AdminAllUsersView.as_view(), name='admin-users-all'),
    path('admin/users/pending/', views.AdminUserListView.as_view(), name='admin-users-pending'),
    path('admin/stats/', views.AdminStatsView.as_view(), name='admin-stats'),
    path('admin/users/<int:user_id>/approve/', views.AdminApproveAgentView.as_view(), name='admin-approve-agent'),
    path('admin/users/<int:user_id>/reject/', views.AdminRejectAgentView.as_view(), name='admin-reject-agent'),

    # ── تغيير دور المستخدم ──────────────────────────────────────────────
    path('change-role/', views.ChangeRoleView.as_view(), name='change-role'),

    # ── إدارة صور الإنجاز (Portfolio) ───────────────────────────────────
    path('portfolio/add/', views.add_portfolio_image, name='add_portfolio_image'),
    path('portfolio/delete/<int:pk>/', views.delete_portfolio_image, name='delete_portfolio_image'),

    # ── إنشاء جلسة Django من توكن JWT (للتكامل مع القوالب￼) ──────────────
    path('django-login/', views.DjangoSessionLoginView.as_view(), name='django-login'),

    path('upload-identity/', views.UploadIdentityView.as_view(), name='upload-identity'),

    # ── إعادة تعيين كلمة المرور ──────────────────────────────────────────
    path('password-reset/request/', views.PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    path('favorites/', views.FavoriteListCreateView.as_view(), name='favorites-list'),
path('favorites/<int:agent_id>/', views.FavoriteDeleteView.as_view(), name='favorites-delete'),
path('featured-agents/', views.FeaturedAgentsView.as_view(), name='featured-agents'),
    path('professionals/', views.ProfessionalListView.as_view(), name='professional-list'),
    path('professionals/<int:pk>/', views.ProfessionalDetailView.as_view(), name='professional-detail'),
    path('professionals/categories/', views.CategoryAPIListView.as_view(), name='professional-categories'),
]