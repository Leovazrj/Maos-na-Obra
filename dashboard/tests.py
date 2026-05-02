from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class DashboardShellTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='gestor@example.com',
            password='segura123',
            name='Gestor',
        )
        self.client.force_login(self.user)

    def test_header_has_dark_mode_toggle_and_safe_profile_dropdown(self):
        response = self.client.get(reverse('dashboard:home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="themeToggle"')
        self.assertContains(response, 'app-theme.js')
        self.assertContains(response, 'app-theme.css')
        self.assertContains(response, 'nxl-user-dropdown')
        self.assertContains(response, 'data-bs-display="static"')
