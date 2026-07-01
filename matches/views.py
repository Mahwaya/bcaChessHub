import json
import re
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import Match


def _parse_game_id(raw):
    """Accept a full Lichess URL or bare game ID; return the game ID string."""
    raw = raw.strip()
    m = re.search(r'lichess\.org/([A-Za-z0-9]{6,12})', raw)
    if m:
        return m.group(1)
    if re.fullmatch(r'[A-Za-z0-9]{6,12}', raw):
        return raw
    return None


@login_required
@require_POST
def link_lichess(request, match_pk):
    match = get_object_or_404(
        Match.objects.select_related('tournament', 'round', 'white_player', 'black_player'),
        pk=match_pk,
    )
    tournament = match.tournament

    user = request.user
    is_director = user.is_staff or (
        hasattr(user, 'member') and
        user.member.role == 'admin' and
        user.member.association_id == tournament.association_id
    )
    if not is_director:
        messages.error(request, 'Only tournament directors can link Lichess games.')
        return redirect('tournament_manage', pk=tournament.pk)

    raw = request.POST.get('lichess_url', '').strip()
    game_id = _parse_game_id(raw)
    if not game_id:
        messages.error(request, 'Invalid Lichess URL or game ID.')
        return redirect('tournament_manage', pk=tournament.pk)

    # ── Fetch game metadata from Lichess API ──────────────────────────
    try:
        req = urllib_request.Request(
            f'https://lichess.org/api/game/{game_id}',
            headers={'Accept': 'application/json'},
        )
        with urllib_request.urlopen(req, timeout=8) as resp:
            game_data = json.loads(resp.read().decode())
    except HTTPError as e:
        if e.code == 404:
            messages.error(request, f'Game "{game_id}" not found on Lichess.')
        else:
            messages.error(request, f'Lichess API error (HTTP {e.code}).')
        return redirect('tournament_manage', pk=tournament.pk)
    except URLError:
        messages.error(request, 'Could not reach Lichess — check your connection.')
        return redirect('tournament_manage', pk=tournament.pk)

    # ── Fetch PGN (optional — never blocks the link) ──────────────────
    pgn_text = ''
    try:
        pgn_url = f'https://lichess.org/game/export/{game_id}?clocks=false&evals=false'
        with urllib_request.urlopen(pgn_url, timeout=8) as resp:
            pgn_text = resp.read().decode()
    except (URLError, HTTPError):
        pass

    # ── Map Lichess result → our RESULT_CHOICES ───────────────────────
    DRAW_STATUSES = {
        'draw', 'stalemate', 'threefoldRepetition', 'repetition',
        'fiftyMoves', 'insufficientMaterial', 'agreement',
    }
    winner = game_data.get('winner')          # 'white', 'black', or absent
    status = game_data.get('status', '')

    if winner == 'white':
        detected = 'white_win'
    elif winner == 'black':
        detected = 'black_win'
    elif status in DRAW_STATUSES or (not winner and status not in ('started', 'created')):
        detected = 'draw'
    else:
        detected = None  # game still in progress

    # ── Persist game ID and PGN ───────────────────────────────────────
    match.lichess_game_id = game_id
    if pgn_text:
        match.pgn = pgn_text
    update_fields = ['lichess_game_id'] + (['pgn'] if pgn_text else [])

    if match.result == 'pending' and detected and match.black_player:
        match.save(update_fields=update_fields)
        match.record_result(detected)
        label = dict(Match.RESULT_CHOICES).get(detected, detected)
        messages.success(request, f'Game {game_id} linked — result auto-recorded: {label}.')
    else:
        match.save(update_fields=update_fields)
        already = match.result != 'pending'
        if detected and already:
            label = dict(Match.RESULT_CHOICES).get(detected, detected)
            messages.success(
                request,
                f'Game {game_id} linked. Result already recorded; Lichess shows: {label}.',
            )
        elif not detected:
            messages.success(request, f'Game {game_id} linked (game may still be in progress).')
        else:
            messages.success(request, f'Game {game_id} linked successfully.')

    return redirect('tournament_manage', pk=tournament.pk)
