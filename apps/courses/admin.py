from django.contrib import admin
from django.utils.html import format_html
from .models import Course, CourseAccess, Purchase, Lesson, LessonProgress, LessonSubmission


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'currency', 'lessons_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'currency', 'created_at')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}

    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'description', 'is_active')
        }),
        ('Цена', {
            'fields': ('price', 'currency')
        }),
        ('Дополнительно', {
            'fields': ('preview_image', 'duration', 'lessons_count'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order', 'is_free', 'duration')
    list_filter = ('course', 'is_free')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('course', 'order')

    fieldsets = (
        ('Основная информация', {
            'fields': ('course', 'title', 'slug', 'description', 'order')
        }),
        ('Контент', {
            'fields': ('video_url', 'content', 'files')
        }),
        ('Настройки', {
            'fields': ('is_free', 'duration')
        }),
    )


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'course', 'amount', 'currency',
                    'status_badge', 'created_at', 'paid_at')
    list_filter = ('status', 'currency', 'created_at', 'paid_at')
    search_fields = ('order_id', 'user__email', 'customer_email', 'course__title')
    readonly_fields = ('order_id', 'created_at', 'updated_at', 'paid_at',
                       'callback_data_display')

    fieldsets = (
        ('Основная информация', {
            'fields': ('order_id', 'user', 'course', 'status')
        }),
        ('Финансовые данные', {
            'fields': ('amount', 'currency')
        }),
        ('Данные покупателя', {
            'fields': ('customer_email', 'customer_name')
        }),
        ('LiqPay', {
            'fields': ('liqpay_order_id', 'payment_id', 'callback_data_display'),
            'classes': ('collapse',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at', 'paid_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        colors = {
            'success': '#10b981',
            'pending': '#f59e0b',
            'processing': '#3b82f6',
            'failure': '#ef4444',
            'reversed': '#6b7280',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )

    status_badge.short_description = 'Статус'

    def callback_data_display(self, obj):
        if obj.callback_data:
            import json
            formatted = json.dumps(obj.callback_data, indent=2, ensure_ascii=False)
            return format_html('<pre style="background: #f5f5f5; padding: 10px;">{}</pre>', formatted)
        return '-'

    callback_data_display.short_description = 'Данные callback'


@admin.register(CourseAccess)
class CourseAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'is_active', 'access_status', 'granted_at', 'expires_at')
    list_filter = ('is_active', 'granted_at', 'expires_at')
    search_fields = ('user__email', 'user__username', 'course__title')
    readonly_fields = ('granted_at',)

    def access_status(self, obj):
        if obj.has_access():
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">✓ Активен</span>'
            )
        return format_html(
            '<span style="color: #ef4444; font-weight: bold;">✗ Истек</span>'
        )

    access_status.short_description = 'Статус доступа'


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'course_title', 'is_completed', 'completed_at')
    list_filter = ('is_completed', 'lesson__course')
    search_fields = ('user__email', 'lesson__title')
    readonly_fields = ('completed_at', 'created_at', 'updated_at')

    def course_title(self, obj):
        return obj.lesson.course.title
    course_title.short_description = 'Курс'


@admin.register(LessonSubmission)
class LessonSubmissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'lesson', 'course_title', 'status_badge', 'created_at', 'file_link')
    list_filter = ('status', 'lesson__course', 'created_at')
    search_fields = ('user__email', 'lesson__title')
    readonly_fields = ('created_at', 'updated_at', 'file_link')

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'lesson', 'status')
        }),
        ('Работа', {
            'fields': ('file_link', 'comment')
        }),
        ('Обратная связь', {
            'fields': ('feedback',)
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def course_title(self, obj):
        return obj.lesson.course.title
    course_title.short_description = 'Курс'

    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b',
            'reviewed': '#3b82f6',
            'approved': '#10b981',
            'rejected': '#ef4444',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Статус'

    def file_link(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank" style="color: #3b82f6;">📎 {}</a>',
                obj.file.url,
                obj.filename
            )
        return '-'
    file_link.short_description = 'Файл'