import logging

from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from tournaments.models import Tournament, TournamentRegistration
from .models import Payment
from .paynow_client import (
    initiate_ecocash,
    initiate_innbucks,
    initiate_web_checkout,
    check_payment_status,
    PAYNOW_SANDBOX,
)

logger = logging.getLogger(__name__)


@login_required
def initiate_payment(request, tournament_pk):
    """GET: show payment form. POST: start Paynow transaction."""
    tournament = get_object_or_404(Tournament, pk=tournament_pk)

    if not hasattr(request.user, 'member'):
        messages.error(request, 'No member profile found.')
        return redirect('tournament_detail', pk=tournament_pk)

    member = request.user.member

    if tournament.registration_fee <= 0:
        messages.info(request, 'This tournament is free — no payment needed.')
        return redirect('tournament_detail', pk=tournament_pk)

    existing = Payment.objects.filter(
        member=member, tournament=tournament, status='completed'
    ).first()
    if existing:
        messages.info(request, 'You have already paid for this tournament.')
        return redirect('tournament_detail', pk=tournament_pk)

    if request.method == 'GET':
        registration = TournamentRegistration.objects.filter(
            tournament=tournament, player=member
        ).first()
        return render(request, 'payments/pay.html', {
            'tournament': tournament,
            'member': member,
            'registration': registration,
            'sandbox': PAYNOW_SANDBOX,
        })

    # POST — create and initiate payment
    gateway = request.POST.get('gateway', 'ecocash')
    phone_number = request.POST.get('phone_number', '').strip()

    if gateway in ('ecocash', 'innbucks') and not phone_number:
        messages.error(request, 'Phone number is required for mobile money payments.')
        return redirect('payment_initiate', tournament_pk=tournament_pk)

    payment = Payment.objects.create(
        member=member,
        tournament=tournament,
        amount=tournament.registration_fee,
        currency=tournament.currency,
        gateway=gateway,
        phone_number=phone_number,
        description=f'Registration fee — {tournament.name}',
        status='pending',
    )

    if gateway == 'ecocash':
        result = initiate_ecocash(payment)
    elif gateway == 'innbucks':
        result = initiate_innbucks(payment)
    else:
        result = initiate_web_checkout(payment)

    if not result.success:
        payment.status = 'failed'
        payment.save(update_fields=['status'])
        messages.error(request, f'Payment initiation failed: {result.error}')
        return redirect('tournament_detail', pk=tournament_pk)

    payment.status = 'awaiting_approval'
    payment.poll_url = result.poll_url
    payment.paynow_reference = result.paynow_reference
    payment.save(update_fields=['status', 'poll_url', 'paynow_reference'])

    if result.redirect_url:
        return redirect(result.redirect_url)

    return render(request, 'payments/awaiting.html', {
        'payment': payment,
        'tournament': tournament,
        'sandbox': PAYNOW_SANDBOX,
    })


@csrf_exempt
def paynow_callback(request):
    """POST callback from Paynow servers on status change."""
    if request.method != 'POST':
        return HttpResponse(status=405)

    try:
        reference = request.POST.get('reference', '')
        status = request.POST.get('status', '').lower()
        paynow_reference = request.POST.get('paynowreference', '')
        gateway_ref = request.POST.get('gateway', '') or paynow_reference
        pk = int(reference.split('-')[-1])
        payment = Payment.objects.get(pk=pk)
    except (ValueError, Payment.DoesNotExist) as e:
        logger.warning('Paynow callback unknown reference: %s', e)
        return HttpResponse('Unknown reference', status=400)

    if status in ('paid', 'awaiting delivery'):
        payment.mark_completed(gateway_reference=gateway_ref)
        try:
            from notifications.email import send_registration_confirmed
            reg = TournamentRegistration.objects.filter(
                tournament=payment.tournament, player=payment.member
            ).first()
            if reg:
                send_registration_confirmed(reg)
        except Exception:
            pass
    elif status in ('cancelled', 'failed'):
        payment.status = status
        payment.save(update_fields=['status'])

    return HttpResponse('OK')


def payment_return(request):
    """GET redirect after Paynow web checkout."""
    paynow_ref = request.GET.get('paynowReference', '')
    payment = Payment.objects.filter(paynow_reference=paynow_ref).first()

    if payment:
        if payment.poll_url:
            live_status = check_payment_status(payment.poll_url)
            if live_status in ('paid', 'awaiting delivery'):
                payment.mark_completed(gateway_reference=paynow_ref)

        return render(request, 'payments/return.html', {
            'payment': payment,
            'tournament': payment.tournament,
        })

    return redirect('home')


@login_required
def poll_payment(request, payment_pk):
    """AJAX: client polls every 5s on the awaiting page."""
    payment = get_object_or_404(Payment, pk=payment_pk, member=request.user.member)

    if payment.status == 'completed':
        return JsonResponse({'status': 'completed', 'redirect': f'/tournaments/{payment.tournament.pk}/'})

    if payment.poll_url and payment.status == 'awaiting_approval':
        live_status = check_payment_status(payment.poll_url)
        if live_status in ('paid', 'awaiting delivery'):
            payment.mark_completed()
            return JsonResponse({'status': 'completed', 'redirect': f'/tournaments/{payment.tournament.pk}/'})
        elif live_status in ('cancelled', 'failed'):
            payment.status = live_status
            payment.save(update_fields=['status'])

    return JsonResponse({'status': payment.status})


# Sandbox views (dev only)

def sandbox_checkout(request, payment_pk):
    if not PAYNOW_SANDBOX:
        return HttpResponse('Sandbox disabled.', status=403)
    payment = get_object_or_404(Payment, pk=payment_pk)
    return render(request, 'payments/sandbox_checkout.html', {'payment': payment})


@require_POST
def sandbox_approve(request, payment_pk):
    if not PAYNOW_SANDBOX:
        return HttpResponse('Sandbox disabled.', status=403)
    payment = get_object_or_404(Payment, pk=payment_pk)
    payment.mark_completed(gateway_reference=f'SANDBOX-{payment_pk}')
    messages.success(request, f'[SANDBOX] {payment.currency} {payment.amount} payment approved.')
    return redirect('tournament_detail', pk=payment.tournament.pk)


def sandbox_poll(request, payment_pk):
    return JsonResponse({'status': 'paid'})
