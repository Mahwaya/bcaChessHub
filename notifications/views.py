from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from .models import Notification


@login_required
def notification_centre(request):
    qs = Notification.objects.filter(recipient=request.user)

    type_filter = request.GET.get('type', '')
    read_filter = request.GET.get('read', '')

    if type_filter:
        qs = qs.filter(type=type_filter)
    if read_filter == 'unread':
        qs = qs.filter(is_read=False)
    elif read_filter == 'read':
        qs = qs.filter(is_read=True)

    # Mark every unread notification in this filtered set as read
    qs.filter(is_read=False).update(is_read=True)

    paginator = Paginator(qs, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))
    params    = request.GET.copy()
    params.pop('page', None)

    return render(request, 'notifications/centre.html', {
        'page_obj': page_obj,
        'type_choices': Notification.TYPE_CHOICES,
        'type_filter': type_filter,
        'read_filter': read_filter,
        'query_string': params.urlencode(),
    })


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('notification_centre')
