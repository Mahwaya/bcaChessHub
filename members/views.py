from django.shortcuts import render
from .models import Member
from associations.models import Association


def rankings(request):
    assoc_filter = request.GET.get('association')
    members = Member.objects.select_related('user', 'association').filter(
        role='player', is_active=True
    ).order_by('-rating')

    if assoc_filter:
        members = members.filter(association__pk=assoc_filter)

    associations = Association.objects.filter(is_active=True)

    return render(request, 'members/rankings.html', {
        'members': members,
        'associations': associations,
        'assoc_filter': assoc_filter,
    })
