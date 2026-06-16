from django.contrib import admin
from .models import Association


@admin.register(Association)
class AssociationAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'country', 'email', 'is_active', 'created_at']
    list_filter = ['country', 'is_active']
    search_fields = ['name', 'city', 'email']
    list_editable = ['is_active']
