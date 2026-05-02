from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from django.test import TestCase
from django.urls import reverse


class EmailAuthenticationFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='autenticacao@example.com',
            password='segura123',
            name='Autenticação',
        )

    def test_login_by_email_redirects_to_dashboard(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': self.user.email,
            'password': 'segura123',
        })

        self.assertRedirects(response, reverse('dashboard:home'))

    def test_authenticated_user_is_redirected_from_login_page(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('accounts:login'))

        self.assertRedirects(response, reverse('dashboard:home'))

    def test_logout_redirects_to_public_home(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse('accounts:logout'))

        self.assertRedirects(response, reverse('pages:home'))


class CustomUserModelTests(TestCase):
    def test_create_user_normalizes_email_and_sets_password(self):
        user = get_user_model().objects.create_user(
            email='User@Example.com',
            password='segura123',
            name='Usuário',
        )

        self.assertEqual(user.email, 'User@example.com')
        self.assertTrue(user.check_password('segura123'))
        self.assertEqual(str(user), 'User@example.com')


class InternalRouteProtectionTests(TestCase):
    def test_dashboard_redirects_anonymous_users_to_login(self):
        response = self.client.get(reverse('dashboard:home'))

        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('dashboard:home')}")


class SignupFlowTests(TestCase):
    def test_signup_page_is_available(self):
        response = self.client.get(reverse('accounts:signup'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cadastre-se')
        self.assertContains(response, 'Nome')
        self.assertContains(response, 'Email')

    def test_signup_creates_user_and_redirects_to_dashboard(self):
        response = self.client.post(reverse('accounts:signup'), {
            'name': 'Novo Usuário',
            'email': 'novo.usuario@example.com',
            'password1': 'Segura123!',
            'password2': 'Segura123!',
        })

        self.assertRedirects(response, reverse('dashboard:home'))
        self.assertTrue(get_user_model().objects.filter(email='novo.usuario@example.com').exists())
        self.assertIn('_auth_user_id', self.client.session)


class PasswordResetFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='recuperacao@example.com',
            password='segura123',
            name='Recuperação',
        )

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
        DEFAULT_FROM_EMAIL='Mãos na Obra <no-reply@maosnaobra.com>',
    )
    def test_password_reset_sends_email_to_registered_user(self):
        response = self.client.post(reverse('accounts:password_reset'), {
            'email': self.user.email,
        })

        self.assertRedirects(response, reverse('accounts:password_reset_done'))
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertIn('Recuperação de Senha', message.subject)
        self.assertIn(self.user.email, message.to)
        self.assertIn('/esqueci-minha-senha/confirmar/', message.body)
        self.assertIn('Mãos na Obra', message.body)
