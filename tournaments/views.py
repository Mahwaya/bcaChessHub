from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Tournament, TournamentRegistration, Round
from matches.models import Match


def tournament_list(request):
    status_filter = request.GET.get('status')
    tournaments = Tournament.objects.select_related('association').all()
    if status_filter:
        tournaments = tournaments.filter(status=status_filter)
    return render(request, 'tournaments/list.html', {
        'tournaments': tournaments,
        'status_filter': status_filter,
    })


def tournament_detail(request, pk):
    tournament = get_object_or_404(Tournament.objects.select_related('association'), pk=pk)
    registrations = tournament.registrations.select_related('player__user').order_by('seed_number', 'registered_at')
    rounds = tournament.rounds.prefetch_related('matches__white_player__user', 'matches__black_player__user').all()

    already_registered = False
    if request.user.is_authenticated and hasattr(request.user, 'member'):
        already_registered = registrations.filter(player=request.user.member).exists()

    return render(request, 'tournaments/detail.html', {
        'tournament': tournament,
        'registrations': registrations,
        'rounds': rounds,
        'already_registered': already_registered,
    })


@login_required
def tournament_register(request, pk):
    tournament = get_object_or_404(Tournament, pk=pk)
    if request.method != 'POST':
        return redirect('tournament_detail', pk=pk)

    if not hasattr(request.user, 'member'):
        messages.error(request, 'You need a member profile to register for tournaments.')
        return redirect('tournament_detail', pk=pk)

    member = request.user.member

    if tournament.status != 'registration_open':
        messages.error(request, 'Registration is not currently open for this tournament.')
        return redirect('tournament_detail', pk=pk)

    if tournament.is_full:
        messages.error(request, 'This tournament is full.')
        return redirect('tournament_detail', pk=pk)

    _, created = TournamentRegistration.objects.get_or_create(
        tournament=tournament,
        player=member,
        defaults={'status': 'pending'}
    )

    if created:
        messages.success(request, f'You have registered for {tournament.name}. Awaiting confirmation.')
    else:
        messages.info(request, 'You are already registered for this tournament.')

    # Email sent when admin confirms (status → confirmed), not on initial pending

    return redirect('tournament_detail', pk=pk)


def tournament_standings(request, pk):
    """Public standings table for a tournament."""
    tournament = get_object_or_404(Tournament.objects.select_related('association'), pk=pk)
    from .services import compute_standings
    standings = compute_standings(tournament)
    rounds = tournament.rounds.order_by('number')
    return render(request, 'tournaments/standings.html', {
        'tournament': tournament,
        'standings': standings,
        'rounds': rounds,
    })


def tournament_round(request, pk, round_number):
    """Public pairings view for a single round."""
    tournament = get_object_or_404(Tournament.objects.select_related('association'), pk=pk)
    round_obj = get_object_or_404(Round, tournament=tournament, number=round_number)
    matches = (
        Match.objects
        .filter(round=round_obj)
        .select_related('white_player__user', 'black_player__user')
        .order_by('board_number')
    )
    rounds = tournament.rounds.order_by('number')
    return render(request, 'tournaments/round.html', {
        'tournament': tournament,
        'round': round_obj,
        'matches': matches,
        'rounds': rounds,
        'viewer_member': request.user.member if request.user.is_authenticated and hasattr(request.user, 'member') else None,
    })
