"""
Tournament service functions — called from views, admin actions, and management commands.
"""

from django.db import transaction
from .models import Round, Tournament
from .pairing import generate_pairings
from matches.models import Match


@transaction.atomic
def create_next_round(tournament):
    """
    Generate pairings for the next round of `tournament`, create the Round
    and Match objects, and return (round, pairings, bye_player, errors).

    Raises ValueError if the tournament is not in a state that allows new rounds.
    """
    if tournament.status not in ('registration_open', 'in_progress'):
        raise ValueError(f'Cannot create a round: tournament status is "{tournament.status}".')

    last_round = tournament.rounds.order_by('-number').first()

    if last_round and not last_round.is_complete:
        raise ValueError(
            f'Round {last_round.number} is not yet complete. '
            'Record all results before generating the next round.'
        )

    next_number = (last_round.number + 1) if last_round else 1

    if next_number > tournament.num_rounds:
        raise ValueError(
            f'All {tournament.num_rounds} rounds have been played. '
            'The tournament is complete.'
        )

    # Update status to in_progress on first round
    if tournament.status == 'registration_open':
        tournament.status = 'in_progress'
        tournament.save(update_fields=['status'])

    round_obj = Round.objects.create(tournament=tournament, number=next_number)

    pairings, bye_player, errors = generate_pairings(tournament, next_number)

    matches = []
    for p in pairings:
        matches.append(Match(
            tournament=tournament,
            round=round_obj,
            white_player=p['white'],
            black_player=p['black'],
            board_number=p['board_number'],
        ))

    # Bye: stored as a match with no black player and auto-win for white
    if bye_player:
        matches.append(Match(
            tournament=tournament,
            round=round_obj,
            white_player=bye_player,
            black_player=None,
            result='white_win',
            board_number=None,
        ))

    Match.objects.bulk_create(matches)

    from django.utils import timezone
    round_obj.started_at = timezone.now()
    round_obj.save(update_fields=['started_at'])

    return round_obj, pairings, bye_player, errors


@transaction.atomic
def complete_round(round_obj):
    """
    Mark a round as complete. Raises ValueError if any matches are still pending.
    """
    pending = round_obj.matches.filter(result='pending', black_player__isnull=False)
    if pending.exists():
        names = ', '.join(
            f'{m.white_player} vs {m.black_player}' for m in pending[:3]
        )
        raise ValueError(f'Pending results remain: {names}{"..." if pending.count() > 3 else ""}')

    from django.utils import timezone
    round_obj.is_complete = True
    round_obj.completed_at = timezone.now()
    round_obj.save(update_fields=['is_complete', 'completed_at'])

    # Auto-complete tournament if this was the final round
    tournament = round_obj.tournament
    if round_obj.number >= tournament.num_rounds:
        tournament.status = 'completed'
        tournament.save(update_fields=['status'])

    return round_obj
