from django.test import TestCase
from django.contrib.auth.models import User
from associations.models import Association
from members.models import Member
from tournaments.models import Tournament, Round, TournamentRegistration
from matches.models import Match, Challenge
import datetime


def make_assoc():
    return Association.objects.create(name='Test Club', city='Bulawayo', email='test@chess.zw')


def make_member(username, rating=1200, assoc=None):
    if assoc is None:
        assoc = make_assoc()
    user = User.objects.create_user(username=username, password='pass1234')
    return Member.objects.create(user=user, association=assoc, rating=rating)


def make_tournament(assoc):
    today = datetime.date.today()
    return Tournament.objects.create(
        association=assoc, name='Test Open', status='in_progress',
        start_date=today, end_date=today, location='Harare', num_rounds=5,
    )


def make_round(tournament, number=1):
    return Round.objects.create(tournament=tournament, number=number)


class MatchEloTest(TestCase):
    def setUp(self):
        self.assoc = make_assoc()
        self.white = make_member('white', 1200, self.assoc)
        self.black = make_member('black', 1200, self.assoc)
        self.tournament = make_tournament(self.assoc)
        self.round = make_round(self.tournament)
        self.match = Match.objects.create(
            tournament=self.tournament, round=self.round,
            white_player=self.white, black_player=self.black,
        )

    def test_white_win_increases_white_elo(self):
        self.match.record_result('white_win')
        self.white.refresh_from_db()
        self.black.refresh_from_db()
        self.assertGreater(self.white.rating, 1200)
        self.assertLess(self.black.rating, 1200)

    def test_black_win_increases_black_elo(self):
        self.match.record_result('black_win')
        self.white.refresh_from_db()
        self.black.refresh_from_db()
        self.assertLess(self.white.rating, 1200)
        self.assertGreater(self.black.rating, 1200)

    def test_draw_equal_players_minimal_change(self):
        self.match.record_result('draw')
        self.white.refresh_from_db()
        self.black.refresh_from_db()
        # Draw between equal players → ratings barely move
        self.assertAlmostEqual(self.white.rating, 1200, delta=2)
        self.assertAlmostEqual(self.black.rating, 1200, delta=2)

    def test_elo_sum_is_conserved(self):
        total_before = self.white.rating + self.black.rating
        self.match.record_result('white_win')
        self.white.refresh_from_db()
        self.black.refresh_from_db()
        total_after = self.white.rating + self.black.rating
        # Due to rounding, allow ±1 deviation
        self.assertAlmostEqual(total_before, total_after, delta=1)

    def test_stronger_player_gains_less_on_win(self):
        strong = make_member('strong', 1600, self.assoc)
        weak   = make_member('weak', 1200, self.assoc)
        m = Match.objects.create(
            tournament=self.tournament, round=self.round,
            white_player=strong, black_player=weak,
        )
        m.record_result('white_win')
        strong.refresh_from_db()
        gain = strong.rating - 1600
        # Expected gain is small (favourite winning) — less than K=32
        self.assertGreater(gain, 0)
        self.assertLess(gain, 10)

    def test_rating_history_created_for_both_players(self):
        from members.models import RatingHistory
        self.match.record_result('white_win')
        self.assertEqual(RatingHistory.objects.filter(member=self.white).count(), 1)
        self.assertEqual(RatingHistory.objects.filter(member=self.black).count(), 1)


class ChallengeEloTest(TestCase):
    def setUp(self):
        self.assoc = make_assoc()
        self.challenger = make_member('challenger', 1200, self.assoc)
        self.opponent   = make_member('opponent', 1200, self.assoc)
        self.challenge  = Challenge.objects.create(
            challenger=self.challenger,
            opponent=self.opponent,
            status='accepted',
        )

    def test_challenger_win_updates_elo(self):
        self.challenge.record_result('challenger_win')
        self.challenger.refresh_from_db()
        self.opponent.refresh_from_db()
        self.assertGreater(self.challenger.rating, 1200)
        self.assertLess(self.opponent.rating, 1200)

    def test_elo_only_updated_once(self):
        """Calling record_result twice must not apply ELO a second time."""
        self.challenge.record_result('challenger_win')
        self.challenger.refresh_from_db()
        rating_after_first = self.challenger.rating

        # Simulate a second call (e.g. double-submit)
        self.challenge.record_result('challenger_win')
        self.challenger.refresh_from_db()
        self.assertEqual(self.challenger.rating, rating_after_first)

    def test_draw_result_sets_status_completed(self):
        self.challenge.record_result('draw')
        self.challenge.refresh_from_db()
        self.assertEqual(self.challenge.status, 'completed')
        self.assertEqual(self.challenge.result, 'draw')
