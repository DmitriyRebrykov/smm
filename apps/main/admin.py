from django.contrib import admin
from django.utils.html import format_html
from .models import ContactRequest, Case, Review


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'service', 'status', 'created_at')
    list_filter = ('status', 'telegram_sent', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at', 'updated_at', 'telegram_sent', 'telegram_message_id')

    fields = (
        'name', 'email', 'service', 'message', 'status',
        'created_at', 'updated_at', 'telegram_sent', 'telegram_message_id'
    )


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'niche', 'order', 'is_active', 'image_preview')
    list_filter = ('category', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('title', 'description', 'niche')

    fieldsets = (
        ('Основное', {
            'fields': ('title', 'category', 'niche', 'description', 'image')
        }),
        ('Метрики', {
            'fields': (('metric_value', 'metric_label'), ('secondary_value', 'secondary_label'))
        }),
        ('Настройки', {
            'fields': ('is_active', 'order')
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;border-radius:4px;">', obj.image.url)
        return '—'
    image_preview.short_description = 'Фото'


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'niche', 'result', 'order', 'is_active', 'avatar_preview')
    list_filter = ('is_active',)
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'niche', 'text')

    fieldsets = (
        ('Автор', {
            'fields': ('name', 'niche', 'avatar')
        }),
        ('Отзыв', {
            'fields': ('text', 'result')
        }),
        ('Настройки', {
            'fields': ('is_active', 'order')
        }),
    )

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" style="height:40px;width:40px;border-radius:50%;object-fit:cover;">', obj.avatar.url)
        return '—'
    avatar_preview.short_description = 'Аватар'