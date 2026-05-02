from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from customers.models import Customer, CustomerInteraction


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

    def test_customer_report_pdf_downloads_as_pdf(self):
        customer = Customer.objects.create(name='Cliente PDF')

        response = self.client.get(reverse('customers:report_pdf', args=[customer.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF'))

    def test_customer_detail_renders_interaction_author_with_custom_user(self):
        customer = Customer.objects.create(name='Cliente Interação')
        CustomerInteraction.objects.create(
            customer=customer,
            user=self.user,
            interaction_type='call',
            interaction_date='2026-05-02',
            description='Contato com o cliente',
        )

        response = self.client.get(reverse('customers:detail', args=[customer.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Registrado por:')
        self.assertContains(response, 'Gestor Cliente')
        self.assertContains(response, 'Histórico de Relacionamento')
        self.assertContains(response, 'Documentos')
        self.assertContains(response, 'Fotos')
        self.assertNotContains(response, 'customerTabs')
