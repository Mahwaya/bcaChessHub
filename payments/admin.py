from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['member', 'tournament', 'amount', 'currency', 'gateway', 'status', 'created_at']
    list_filter = ['status', 'gateway', 'currency']
    search_fields = ['member__user__last_name', 'gateway_reference']
    readonly_fields = ['created_at', 'completed_at']
