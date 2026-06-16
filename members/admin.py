from django.contrib import admin
from .models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'association', 'role', 'rating', 'is_active', 'joined_at']
    list_filter = ['role', 'association', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'user__email']
    list_editable = ['rating', 'is_active']
    readonly_fields = ['joined_at']
    autocomplete_fields = ['user', 'association']
