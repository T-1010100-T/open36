"""
Post admin configuration
"""
from django.contrib import admin
from .models import Post, PostEditHistory


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'author_id', 'section_id', 'status', 'is_pinned', 'views_count', 'created_at')
    list_display_links = ('id', 'title')
    search_fields = ('title', 'content')
    list_filter = ('status', 'is_pinned', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('内容', {
            'fields': ('title', 'content')
        }),
        ('元数据', {
            'fields': ('author_id', 'section_id', 'status', 'is_pinned', 'pin_type')
        }),
        ('统计', {
            'fields': ('views_count', 'edit_count')
        }),
        ('时间', {
            'fields': ('created_at', 'updated_at', 'last_edited_at', 'last_edited_by'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PostEditHistory)
class PostEditHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'post', 'edited_by', 'created_at')
    list_display_links = ('id',)
    search_fields = ('title', 'content')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
