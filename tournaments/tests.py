import datetime
from django.test import TestCase
from django.contrib.auth.models import User
from associations.models import Association
from members.models import Member
from .models import Tournament, TournamentRegistration, Round
from .pairing import generate_pairings, _score
from matches.models import Match


def make_assoc():
    return Association.objects.create(name='Test Club', city='Bulawayo', email='test@chess.zw')


def make_member(username, rating=1200, assoc=None):
    if assoc is None:
        assoc = make_assoc()
    user = User.objects.create_user(username=username, password='pass1234')
    return Member.objects.create(user=user, association=assoc, rating=rating)


def make_tournament(assoc, num_rounds=5):
    today = datetime.date.today()
    return Tournament.objects.create(
        association=assoc, name='Test Open', status='in_progress',
        start_date=today, end_date=today, location='Harare',
        num_rounds=num_rounds,
    )


def register(player, tournament):
    return TournamentRegistration.objects.create(
        tournament=tournament, player=player, status='confirmed'
    )


class ScoreHelperTest(TestCase):
    def setUp(self):
        self.assoc = make_assoc()
        self.p1 = make_member('p1', assoc=self.assoc)
        self.p2 = make_member('p2', assoc=self.assoc)
        self.tournament = make_tournament(self.assoc)
        self.round = Round.objects.create(tournament=self.tournament, number=1)

    def _make_match(self, white, black, result):
        return Match.objects.create(
            tournament=self.tournament, round=self.round,
            white_player=white, black_player=black, result=result,
        )

    def test_win_gives_one_point(self):
        self._make_match(self.p1, self.p2, 'white_win')
        self.assertEqual(_score(self.p1, self.tournament), 1.0)

    def test_loss_gives_zero_points(self):
        self._make_match(self.p1, self.p2, 'white_win')
        self.assertEqual(_score(self.p2, self.tournament), 0.0)

    def test_draw_gives_half_point(self):
        self._make_match(self.p1, self.p2, 'draw')
        self.assertEqual(_score(self.p1, self.tournament), 0.5)
        self.assertEqual(_score(self.p2, self.tournament), 0.5)

    def test_pending_match_not_counted(self):
        self._make_match(self.p1, self.p2, 'pending')
        self.assertEqual(_score(self.p1, self.tournament), 0.0)


class SwissPairingTest(TestCase):
    def setUp(self):
        self.assoc = make_assoc()
        self.tournament = make_tournament(self.assoc)
        # Create 4 players with different ratings
        self.players = [
            make_member(f'p{i}', rating=1200 + i * 50, assoc=self.assoc)
            for i in range(4)
        ]
        for p in self.players:
            register(p, self.tournament)

    def test_generates_correct_number_of_pairings(self):
        pairings, bye, errors = generate_pairings(self.tournament, 1)
        self.assertEqual(len(pairings), 2)  # 4 players → 2 boards
        self.assertIsNone(bye)

    def test_each_player_appears_once(self):
        pairings, _, _ = generate_pairings(self.tournament, 1)
        assigned = set()
        for p in pairings:
            assigned.add(p['white'].pk)
            assigned.add(p['black'].pk)
        self.assertEqual(len(assigned), 4)

    def test_no_rematches_in_round_2(self):
        # Run round 1 and record results
        round1 = Round.objects.create(tournament=self.tournament, number=1)
        pairings1, _, _ = generate_pairings(self.tournament, 1)
        for pair in pairings1:
            Match.objects.create(
                tournament=self.tournament, round=round1,
                white_player=pair['white'], black_player=pair['black'],
                result='white_win',
            )
        # Round 2 pairings must not repeat round 1 matchups
        pairings2, _, _ = generate_pairings(self.tournament, 2)
        r1_pairs = {frozenset([p['white'].pk, p['black'].pk]) for p in pairings1}
        for pair in pairings2:
            matchup = frozenset([pair['white'].pk, pair['black'].pk])
            self.assertNotIn(matchup, r1_pairs)

    def test_bye_assigned_for_odd_players(self):
        extra = make_member('p_extra', rating=1100, assoc=self.assoc)
        register(extra, self.tournament)  # now 5 players
        pairings, bye, _ = generate_pairings(self.tournament, 1)
        self.assertEqual(len(pairings), 2)
        self.assertIsNotNone(bye)

    def test_empty_tournament_returns_error(self):
        empty_t = make_tournament(self.assoc)
        pairings, bye, errors = generate_pairings(empty_t, 1)
        self.assertEqual(pairings, [])
        self.assertTrue(len(errors) > 0)
