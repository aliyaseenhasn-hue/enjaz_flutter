from django.contrib import admin
from .models import Category, ServiceRequest, RequestAttachment, RequestTimeline, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    search_fields = ('name',)


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'customer', 'agent', 'status', 'estimated_price', 'created_at')
    list_filter = ('status', 'category')
    search_fields = ('title', 'customer__phone_number', 'agent__phone_number')
    raw_id_fields = ('customer', 'agent')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('request', 'rating', 'reviewer', 'reviewee', 'review_type', 'created_at')
    list_filter = ('rating', 'review_type')
