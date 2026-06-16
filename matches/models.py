from django.db import models
from members.models import Member
from tournaments.models import Tournament, Round


class Match(models.Model):
    RESULT_CHOICES = [
        ('white_win', 'White Wins (1-0)'),
        ('black_win', 'Black Wins (0-1)'),
        ('draw', 'Draw (½-½)'),
        ('white_forfeit', 'White Forfeits'),
        ('black_forfeit', 'Black Forfeits'),
        ('pending', 'Not Yet Played'),
    ]

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='matches')
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name='matches')
    white_player = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='matches_as_white')
    black_player = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='matches_as_black')
    result = models.CharField(max_length=20, choices=RESULT_CHOICES, default='pending')
    scheduled_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    board_number = models.PositiveIntegerField(blank=True, null=True)
    pgn = models.TextField(blank=True, help_text='Game in PGN notation for analysis')
    lichess_game_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['round__number', 'board_number']

    def __str__(self):
        return f"{self.white_player} vs {self.black_player} (Round {self.round.number})"

    def record_result(self, result):
        self.result = result
        from django.utils import timezone
        self.completed_at = timezone.now()
        self.save(update_fields=['result', 'completed_at'])
        self._update_elo_ratings()

    def _update_elo_ratings(self):
        K = 32
        white = self.white_player
        black = self.black_player
        expected_white = 1 / (1 + 10 ** ((black.rating - white.rating) / 400))
        expected_black = 1 - expected_white

        if self.result == 'white_win':
            score_white, score_black = 1, 0
        elif self.result == 'black_win':
            score_white, score_black = 0, 1
        else:
            score_white, score_black = 0.5, 0.5

        white.update_rating(round(white.rating + K * (score_white - expected_white)))
        black.update_rating(round(black.rating + K * (score_black - expected_black)))
