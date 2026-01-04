from django.contrib import admin
from .models import ContactRequest


@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'email', 'service', 'status', 'created_at')
    list_filter = ('status', 'telegram_sent', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at', 'updated_at', 'telegram_sent', 'telegram_message_id')
    
    # Упрощенная версия без fieldsets для избежания проблем с Python 3.14
    fields = (
        'name', 'email', 'service', 'message', 'status',
        'created_at', 'updated_at', 'telegram_sent', 'telegram_message_id'
    )