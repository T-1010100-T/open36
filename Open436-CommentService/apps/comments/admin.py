"""
Comment admin configuration
"""
from django.contrib import admin
from .models import Reply, PostLike, PostFavorite


@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ('id', 'post_id', 'author_id', 'floor_number', 'is_deleted', 'created_at')
    list_display_links = ('id',)
    search_fields = ('content',)
    list_filter = ('is_deleted', 'created_at')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)

    fieldsets = (
        ('内容', {
            'fields': ('content',)
        }),
        ('元数据', {
            'fields': ('post_id', 'author_id', 'floor_number', 'is_deleted')
        }),
        ('时间', {
            'fields': ('created_at', 'updated_at', 'last_edited_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'post_id', 'user_id', 'created_at')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(PostFavorite)
class PostFavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'post_id', 'user_id', 'created_at')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
