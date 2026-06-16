from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'type', 'is_read', 'email_sent', 'sent_at']
    list_filter = ['type', 'is_read', 'email_sent']
    search_fields = ['recipient__username', 'message']
    readonly_fields = ['sent_at']
