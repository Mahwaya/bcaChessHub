from django.shortcuts import redirect
from django.urls import reverse


_EXEMPT = frozenset([
    '/login/',
    '/logout/',
    '/signup/',
    '/2fa/verify/',
    '/admin/',
])


class TwoFactorMiddleware:
    """
    After a normal login, if the user's member has 2FA enabled and the
    session hasn't been 2FA-verified yet, redirect every request to the
    TOTP verification page.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and not request.session.get('2fa_verified')
            and hasattr(request.user, 'member')
            and request.user.member.totp_enabled
            and not self._is_exempt(request.path)
        ):
            verify_url = reverse('verify_2fa')
            if request.path != verify_url:
                return redirect(f'{verify_url}?next={request.path}')

        return self.get_response(request)

    def _is_exempt(self, path):
        return any(path.startswith(e) for e in _EXEMPT)
