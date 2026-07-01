from django.db import models
from members.models import Member
from tournaments.models import Tournament


class Payment(models.Model):
    GATEWAY_CHOICES = [
        ('ecocash', 'EcoCash'),
        ('innbucks', 'InnBucks'),
        ('paypal', 'PayPal'),
        ('visa', 'VISA / Mastercard'),
        ('cash', 'Cash'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('awaiting_approval', 'Awaiting Phone Approval'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='payments')
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.CharField(max_length=300, blank=True)

    # Paynow-specific fields
    paynow_reference = models.CharField(max_length=200, blank=True, help_text='Paynow internal reference')
    gateway_reference = models.CharField(max_length=200, blank=True, help_text='Transaction ID from payment provider')
    poll_url = models.URLField(max_length=500, blank=True, help_text='Paynow poll URL for status checks')
    phone_number = models.CharField(max_length=20, blank=True, help_text='Mobile money phone number')

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.member} — {self.currency} {self.amount} via {self.gateway} ({self.status})"

    def mark_completed(self, gateway_reference=''):
        from django.utils import timezone
        self.status = 'completed'
        self.gateway_reference = gateway_reference
        self.completed_at = timezone.now()
        self.save(update_fields=['status', 'gateway_reference', 'completed_at'])
        self._confirm_registration()

    def _confirm_registration(self):
        """Auto-confirm tournament registration once payment clears."""
        if not self.tournament:
            return
        from tournaments.models import TournamentRegistration
        TournamentRegistration.objects.filter(
            tournament=self.tournament,
            player=self.member,
            status='pending',
        ).update(status='confirmed')
