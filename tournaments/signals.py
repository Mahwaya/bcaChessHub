from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import TournamentRegistration


@receiver(pre_save, sender=TournamentRegistration)
def on_registration_confirmed(sender, instance, **kwargs):
    """Send confirmation email when an admin moves status to 'confirmed'."""
    if not instance.pk:
        return
    try:
        previous = TournamentRegistration.objects.get(pk=instance.pk)
    except TournamentRegistration.DoesNotExist:
        return

    if previous.status != 'confirmed' and instance.status == 'confirmed':
        from notifications.email import send_registration_confirmed
        send_registration_confirmed(instance)
