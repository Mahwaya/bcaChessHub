from django.contrib import admin
from .models import Match


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'tournament', 'round', 'result', 'board_number', 'scheduled_at']
    list_filter = ['result', 'tournament', 'round']
    search_fields = ['white_player__user__last_name', 'black_player__user__last_name']
    list_editable = ['result']
    readonly_fields = ['completed_at']
