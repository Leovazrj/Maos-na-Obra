from django.test import TestCase
from django.urls import reverse


class HomePageTests(TestCase):
    def test_home_page_exposes_login_action_only(self):
        response = self.client.get(reverse('pages:home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Entrar')
        self.assertNotContains(response, 'Cadastre-se')
        self.assertNotContains(response, reverse('accounts:signup'))
        self.assertContains(response, reverse('accounts:login'))

    def test_home_page_loads_custom_button_styles(self):
        response = self.client.get(reverse('pages:home'))

        self.assertContains(response, 'custom/css/app-theme.css')
