from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from customers.models import Customer


class CustomerViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='gestor.cliente@example.com',
            password='segura123',
            name='Gestor Cliente',
        )
        self.client.force_login(self.user)

    def test_customer_create_view_persists_customer_and_redirects(self):
        response = self.client.post(reverse('customers:create'), {
            'name': 'Cliente Novo',
            'person_type': 'J',
            'document_number': '12.345.678/0001-90',
            'email': 'cliente.novo@example.com',
            'phone': '(11) 99999-9999',
            'address': 'Rua das Obras, 100',
            'status': 'active',
        })

        customer = Customer.objects.get(name='Cliente Novo')
        self.assertRedirects(response, reverse('customers:list'))
        self.assertEqual(customer.email, 'cliente.novo@example.com')
