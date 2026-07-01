from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.db.models import Q
from .models import Member
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
