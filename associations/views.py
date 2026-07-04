from django.shortcuts import render, get_object_or_404
from .models import Association
from members.models import Member
from tournaments.models import Tournament
from matches.models import Match


def association_list(request):
    associations = Association.objects.filter(is_active=True)

    rows = []
    for assoc in associations:
        rows.append({
            'assoc': assoc,
            'member_count': Member.objects.filter(association=assoc, is_active=True).count(),
            'tournament_count': Tournament.objects.filter(association=assoc).count(),
            'active_tournaments': Tournament.objects.filter(
                association=assoc, status__in=('registration_open', 'in_progress')
            ).count(),
        })

    return render(request, 'associations/list.html', {'rows': rows})


def association_detail(request, pk):
    assoc = get_object_or_404(Association, pk=pk, is_active=True)

    members = Member.objects.filter(
        association=assoc, is_active=True
    ).select_related('user').order_by('-rating')

    top_players = members.filter(role='player')[:8]

    active_tournaments = Tournament.objects.filter(
        association=assoc, status__in=('registration_open', 'in_progress')
    ).order_by('start_date')

    recent_tournaments = Tournament.objects.filter(
        association=assoc, status='completed'
    ).order_by('-end_date')[:5]

    upcoming_tournaments = Tournament.objects.filter(
        association=assoc, status='upcoming'
    ).order_by('start_date')[:3]

    games_played = Match.objects.filter(
        tournament__association=assoc, black_player__isnull=False
    ).exclude(result='pending').count()

    stats = {
        'members':     members.count(),
        'players':     members.filter(role='player').count(),
        'coaches':     members.filter(role='coach').count(),
        'tournaments': Tournament.objects.filter(association=assoc).count(),
        'games':       games_played,
    }

    return render(request, 'associations/detail.html', {
        'assoc': assoc,
        'stats': stats,
        'top_players': top_players,
        'active_tournaments': active_tournaments,
        'upcoming_tournaments': upcoming_tournaments,
        'recent_tournaments': recent_tournaments,
    })
