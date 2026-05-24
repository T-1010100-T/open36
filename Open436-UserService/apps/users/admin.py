"""
User admin configuration
"""
from django.contrib import admin
from .models import UserProfile, UserStatistics


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'nickname', 'avatar_url', 'created_at', 'updated_at')
    list_display_links = ('user_id', 'nickname')
    search_fields = ('nickname', 'bio')
    list_filter = ('created_at',)
    readonly_fields = ('user_id', 'created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('基本信息', {
            'fields': ('user_id', 'nickname')
        }),
        ('个人资料', {
            'fields': ('avatar_url', 'bio')
        }),
        ('时间信息', {
            'fields': ('nickname_updated_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserStatistics)
class UserStatisticsAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'posts_count', 'replies_count', 'likes_received', 'favorites_received', 'updated_at')
    list_display_links = ('user_id',)
    search_fields = ('user__nickname',)
    readonly_fields = ('updated_at',)
    ordering = ('-posts_count',)
