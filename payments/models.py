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
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='payments')
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name='payments', null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    gateway_reference = models.CharField(max_length=200, blank=True, help_text='Transaction ID from payment provider')
    description = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.member} — {self.currency} {self.amount} via {self.gateway} ({self.status})"
