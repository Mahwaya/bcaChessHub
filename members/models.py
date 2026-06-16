from django.db import models
from django.contrib.auth.models import User
from associations.models import Association


class Member(models.Model):
    ROLE_CHOICES = [
        ('player', 'Player'),
        ('coach', 'Coach'),
        ('admin', 'Administrator'),
        ('parent', 'Parent'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='member')
    association = models.ForeignKey(Association, on_delete=models.CASCADE, related_name='members')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='player')
    phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    rating = models.IntegerField(default=1200)  # ELO rating, starts at 1200
    rank = models.CharField(max_length=50, blank=True)
    profile_photo = models.ImageField(upload_to='member_photos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    # Parent-child relationship for parental monitoring (from UML)
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='children', limit_choices_to={'role': 'parent'}
    )

    class Meta:
        ordering = ['-rating']

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.association.name})"

    def update_rating(self, new_rating):
        self.rating = new_rating
        self.save(update_fields=['rating'])
