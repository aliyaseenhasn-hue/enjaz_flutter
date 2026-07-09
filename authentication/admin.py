from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, AgentProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('phone_number', 'first_name', 'last_name', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active')
    search_fields = ('phone_number', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('المعلومات الشخصية', {'fields': ('first_name', 'last_name', 'avatar')}),
        ('الصلاحيات', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'verification_status', 'is_verified', 'balance', 'rating', 'total_jobs')
    list_filter = ('verification_status', 'is_verified')
    search_fields = ('user__phone_number', 'user__first_name')
    actions = ['approve_agents', 'reject_agents']

    @admin.action(description='قبول المندوبين المحددين')
    def approve_agents(self, request, queryset):
        queryset.update(is_verified=True, verification_status='approved')

    @admin.action(description='رفض المندوبين المحددين')
    def reject_agents(self, request, queryset):
        queryset.update(verification_status='rejected')


