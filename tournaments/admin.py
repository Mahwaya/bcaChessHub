from django.contrib import admin
from .models import Tournament, TournamentRegistration, Round


class RoundInline(admin.TabularInline):
    model = Round
    extra = 0
    readonly_fields = ['is_complete', 'started_at', 'completed_at']


class RegistrationInline(admin.TabularInline):
    model = TournamentRegistration
    extra = 0
    readonly_fields = ['registered_at']


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ['name', 'association', 'format', 'status', 'start_date', 'end_date', 'player_count', 'max_players']
    list_filter = ['status', 'format', 'association']
    search_fields = ['name', 'location']
    list_editable = ['status']
    readonly_fields = ['created_at']
    inlines = [RegistrationInline, RoundInline]

    def player_count(self, obj):
        return obj.player_count
    player_count.short_description = 'Players'


@admin.register(TournamentRegistration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['player', 'tournament', 'status', 'registered_at']
    list_filter = ['status', 'tournament']
    list_editable = ['status']
