from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.db.models import Q
from .models import Member, RatingHistory
from .forms import SignupForm
from associations.models import Association
from matches.models import Match
from notifications.models import Notification


def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to ChessHub, {user.first_name}!')
            return redirect('dashboard')
    else:
        form = SignupForm()

    return render(request, 'registration/signup.html', {'form': form})


@login_required
def dashboard(request):
    if not hasattr(request.user, 'member'):
        return redirect('home')

    member = request.user.member

    # All matches this member played (completed only)
    matches_as_white = Match.objects.filter(
        white_player=member
    ).exclude(result='pending').select_related('tournament', 'round', 'black_player__user')

    matches_as_black = Match.objects.filter(
        black_player=member
    ).exclude(result='pending').select_related('tournament', 'round', 'white_player__user')

    wins = (
        matches_as_white.filter(result='white_win').count() +
        matches_as_black.filter(result='black_win').count()
    )
    losses = (
        matches_as_white.filter(result='black_win').count() +
        matches_as_black.filter(result='white_win').count()
    )
    draws = (
        matches_as_white.filter(result='draw').count() +
        matches_as_black.filter(result='draw').count()
    )
    games_played = wins + losses + draws

    if games_played > 0:
        win_rate = round(wins / games_played * 100)
        draw_rate = round(draws / games_played * 100)
        loss_rate = 100 - win_rate - draw_rate
    else:
        win_rate = draw_rate = loss_rate = 0

    # Combine and sort recent matches by date
    from itertools import chain
    all_matches = sorted(
        chain(matches_as_white, matches_as_black),
        key=lambda m: m.completed_at or m.scheduled_at or m.round.started_at or m.tournament.start_date,
        reverse=True
    )[:15]

    registrations = member.registrations.select_related(
        'tournament__association'
    ).order_by('-tournament__start_date')

    unread_qs = Notification.objects.filter(recipient=request.user, is_read=False)
    unread_qs.update(is_read=True)
    notifications = unread_qs.order_by('-sent_at')[:5]

    return render(request, 'members/dashboard.html', {
        'member': member,
        'stats': {
            'games_played': games_played,
            'wins': wins,
            'losses': losses,
            'draws': draws,
            'win_rate': win_rate,
            'draw_rate': draw_rate,
            'loss_rate': loss_rate,
        },
        'recent_matches': all_matches,
        'registrations': registrations,
        'notifications': notifications,
    })


@login_required
def manage_members(request):
    """Association admin panel — view and manage all members."""
    if not (request.user.is_staff or (hasattr(request.user, 'member') and request.user.member.role == 'admin')):
        messages.error(request, 'Only administrators can access member management.')
        return redirect('dashboard')

    # Staff sees all; association admin sees only their association
    if request.user.is_staff:
        base_qs = Member.objects.select_related('user', 'association')
    else:
        base_qs = Member.objects.select_related('user', 'association').filter(
            association=request.user.member.association
        )

    if request.method == 'POST':
        action     = request.POST.get('action')
        member_pk  = request.POST.get('member_pk')
        target     = get_object_or_404(base_qs, pk=member_pk)

        if action == 'set_role':
            new_role = request.POST.get('role')
            valid_roles = [r[0] for r in Member.ROLE_CHOICES]
            if new_role in valid_roles:
                target.role = new_role
                target.save(update_fields=['role'])
                messages.success(request, f'{target} role changed to {target.get_role_display()}.')

        elif action == 'toggle_active':
            target.is_active = not target.is_active
            target.save(update_fields=['is_active'])
            state = 'activated' if target.is_active else 'deactivated'
            messages.success(request, f'{target} {state}.')

        elif action == 'reset_elo':
            if request.user.is_staff:
                target.rating = 1200
                target.save(update_fields=['rating'])
                RatingHistory.objects.create(member=target, rating=1200, delta=0)
                messages.success(request, f'{target} ELO reset to 1200.')
            else:
                messages.error(request, 'Only site staff can reset ELO ratings.')

        return redirect('manage_members')

    # GET — filters
    role_filter   = request.GET.get('role', '')
    status_filter = request.GET.get('status', 'active')
    search        = request.GET.get('q', '').strip()

    qs = base_qs
    if role_filter:
        qs = qs.filter(role=role_filter)
    if status_filter == 'active':
        qs = qs.filter(is_active=True)
    elif status_filter == 'inactive':
        qs = qs.filter(is_active=False)
    if search:
        qs = qs.filter(
            user__first_name__icontains=search
        ) | qs.filter(
            user__last_name__icontains=search
        ) | qs.filter(
            user__username__icontains=search
        )

    qs = qs.order_by('-rating')

    # Summary counts (unfiltered)
    all_members = base_qs
    summary = {
        'total':    all_members.count(),
        'active':   all_members.filter(is_active=True).count(),
        'players':  all_members.filter(role='player').count(),
        'admins':   all_members.filter(role='admin').count(),
        'coaches':  all_members.filter(role='coach').count(),
    }

    return render(request, 'members/manage.html', {
        'members': qs,
        'summary': summary,
        'role_choices': Member.ROLE_CHOICES,
        'role_filter': role_filter,
        'status_filter': status_filter,
        'search': search,
        'can_reset_elo': request.user.is_staff,
    })


def player_profile(request, pk):
    member = get_object_or_404(
        Member.objects.select_related('user', 'association'),
        pk=pk, is_active=True,
    )

    # Match stats
    white_matches = Match.objects.filter(white_player=member).exclude(result='pending').select_related('tournament', 'round', 'black_player__user')
    black_matches = Match.objects.filter(black_player=member).exclude(result='pending').select_related('tournament', 'round', 'white_player__user')

    wins   = white_matches.filter(result__in=['white_win','black_forfeit']).count() + black_matches.filter(result__in=['black_win','white_forfeit']).count()
    losses = white_matches.filter(result__in=['black_win','white_forfeit']).count() + black_matches.filter(result__in=['white_win','black_forfeit']).count()
    draws  = white_matches.filter(result='draw').count() + black_matches.filter(result='draw').count()
    games  = wins + losses + draws

    from itertools import chain
    recent_matches = sorted(
        chain(white_matches, black_matches),
        key=lambda m: m.completed_at or m.scheduled_at or m.round.started_at,
        reverse=True
    )[:12]

    # Tournament history
    from tournaments.models import TournamentRegistration
    from tournaments.services import compute_standings
    registrations = member.registrations.select_related('tournament__association').order_by('-tournament__start_date')

    tournament_rows = []
    for reg in registrations:
        t = reg.tournament
        row = {'tournament': t, 'status': reg.status}
        if t.status in ('in_progress', 'completed'):
            standings = compute_standings(t)
            entry = next((s for s in standings if s['player'].pk == member.pk), None)
            if entry:
                row.update({'score': entry['score'], 'rank': entry['rank'], 'total': len(standings)})
        tournament_rows.append(row)

    # Rating history for chart
    history = list(member.rating_history.order_by('recorded_at').values('rating', 'delta', 'recorded_at'))
    import json
    from django.utils.timezone import localtime
    chart_labels = [localtime(h['recorded_at']).strftime('%d %b %Y') for h in history]
    chart_data   = [h['rating'] for h in history]
    # Prepend starting point (1200) if we have history
    if chart_data:
        chart_labels = ['Start (1200)'] + chart_labels
        chart_data   = [1200] + chart_data

    return render(request, 'members/profile.html', {
        'member': member,
        'wins': wins, 'losses': losses, 'draws': draws, 'games': games,
        'win_pct': round(wins / games * 100) if games else 0,
        'recent_matches': recent_matches,
        'tournament_rows': tournament_rows,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'is_own_profile': request.user.is_authenticated and hasattr(request.user, 'member') and request.user.member.pk == member.pk,
    })


def rankings(request):
    assoc_filter = request.GET.get('association')
    members = Member.objects.select_related('user', 'association').filter(
        role='player', is_active=True
    ).order_by('-rating')

    if assoc_filter:
        members = members.filter(association__pk=assoc_filter)

    associations = Association.objects.filter(is_active=True)

    return render(request, 'members/rankings.html', {
        'members': members,
        'associations': associations,
        'assoc_filter': assoc_filter,
    })
