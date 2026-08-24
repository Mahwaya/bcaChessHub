import pyotp
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from associations.models import Association
from .models import Member, RatingHistory


def make_association():
    return Association.objects.create(
        name='Test Chess Club', city='Harare', email='club@test.com'
    )


def make_user_and_member(username='alice', rating=1200, assoc=None, totp_enabled=False):
    if assoc is None:
        assoc = make_association()
    user = User.objects.create_user(
        username=username, password='pass1234', email=f'{username}@test.com',
        first_name='Alice', last_name='Test'
    )
    member = Member.objects.create(user=user, association=assoc, rating=rating)
    if totp_enabled:
        secret = pyotp.random_base32()
        member.totp_secret = secret
        member.totp_enabled = True
        member.save()
    return user, member


class SignupViewTest(TestCase):
    def setUp(self):
        self.assoc = make_association()
        self.client = Client()

    def test_signup_creates_user_and_member(self):
        response = self.client.post(reverse('signup'), {
            'username': 'newplayer',
            'first_name': 'New',
            'last_name': 'Player',
            'email': 'new@test.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'association': self.assoc.pk,
        })
        self.assertEqual(User.objects.filter(username='newplayer').count(), 1)
        self.assertEqual(Member.objects.filter(user__username='newplayer').count(), 1)

    def test_signup_sets_default_elo(self):
        self.client.post(reverse('signup'), {
            'username': 'newplayer',
            'first_name': 'New',
            'last_name': 'Player',
            'email': 'new@test.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'association': self.assoc.pk,
        })
        member = Member.objects.get(user__username='newplayer')
        self.assertEqual(member.rating, 1200)


class EloAndRatingHistoryTest(TestCase):
    def setUp(self):
        self.assoc = make_association()
        _, self.member = make_user_and_member('player1', assoc=self.assoc)

    def test_update_rating_changes_rating(self):
        self.member.update_rating(1216)
        self.member.refresh_from_db()
        self.assertEqual(self.member.rating, 1216)

    def test_update_rating_creates_history_record(self):
        self.member.update_rating(1216)
        history = RatingHistory.objects.filter(member=self.member)
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().rating, 1216)
        self.assertEqual(history.first().delta, 16)

    def test_update_rating_negative_delta(self):
        self.member.update_rating(1184)
        self.member.refresh_from_db()
        self.assertEqual(self.member.rating, 1184)
        self.assertEqual(RatingHistory.objects.get(member=self.member).delta, -16)


class TwoFactorMiddlewareTest(TestCase):
    def setUp(self):
        self.assoc = make_association()
        self.user_no2fa, _ = make_user_and_member('no2fa', assoc=self.assoc)
        self.user_2fa, self.member_2fa = make_user_and_member('with2fa', assoc=self.assoc, totp_enabled=True)
        self.client = Client()

    def test_no_2fa_user_can_reach_dashboard(self):
        self.client.login(username='no2fa', password='pass1234')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_2fa_user_redirected_to_verify(self):
        self.client.login(username='with2fa', password='pass1234')
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"{reverse('verify_2fa')}?next={reverse('dashboard')}")

    def test_2fa_user_with_session_flag_can_reach_dashboard(self):
        self.client.login(username='with2fa', password='pass1234')
        session = self.client.session
        session['2fa_verified'] = True
        session.save()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)


class TwoFactorVerifyViewTest(TestCase):
    def setUp(self):
        self.assoc = make_association()
        self.user, self.member = make_user_and_member('with2fa', assoc=self.assoc, totp_enabled=True)
        self.client = Client()
        self.client.login(username='with2fa', password='pass1234')

    def test_correct_code_sets_session_flag(self):
        totp = pyotp.TOTP(self.member.totp_secret)
        response = self.client.post(reverse('verify_2fa'), {
            'code': totp.now(),
            'next': '',
        })
        self.assertTrue(self.client.session.get('2fa_verified'))

    def test_wrong_code_shows_error(self):
        response = self.client.post(reverse('verify_2fa'), {
            'code': '000000',
            'next': '',
        })
        self.assertFalse(self.client.session.get('2fa_verified'))
        self.assertContains(response, 'Invalid code')


class TwoFactorSetupViewTest(TestCase):
    def setUp(self):
        self.assoc = make_association()
        self.user, self.member = make_user_and_member('setup_user', assoc=self.assoc)
        self.client = Client()
        self.client.login(username='setup_user', password='pass1234')

    def test_generate_stores_secret_in_session(self):
        self.client.post(reverse('setup_2fa'), {'action': 'generate'})
        self.assertIn('pending_totp_secret', self.client.session)

    def test_confirm_with_valid_code_enables_2fa(self):
        self.client.post(reverse('setup_2fa'), {'action': 'generate'})
        secret = self.client.session['pending_totp_secret']
        code = pyotp.TOTP(secret).now()
        self.client.post(reverse('setup_2fa'), {'action': 'confirm', 'code': code})
        self.member.refresh_from_db()
        self.assertTrue(self.member.totp_enabled)
        self.assertEqual(self.member.totp_secret, secret)

    def test_confirm_with_wrong_code_does_not_enable_2fa(self):
        self.client.post(reverse('setup_2fa'), {'action': 'generate'})
        self.client.post(reverse('setup_2fa'), {'action': 'confirm', 'code': '000000'})
        self.member.refresh_from_db()
        self.assertFalse(self.member.totp_enabled)
