from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from customers.models import Customer, CustomerDocument, CustomerPhoto
from projects.models import PhysicalMeasurement, Project, ProjectTask

from client_portal.models import ClientPortalAccess


class ClientPortalModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='portal@example.com',
            password='segura123',
            name='Portal',
        )
        self.customer = Customer.objects.create(name='Cliente Portal', email='portal@cliente.com')

    def test_access_model_is_timestamped(self):
        access = ClientPortalAccess.objects.create(customer=self.customer, user=self.user)

        self.assertEqual(str(access), 'Portal - Cliente Portal')
        self.assertTrue(access.is_active)
        self.assertEqual(access.customer, self.customer)
        self.assertEqual(access.user, self.user)


class ClientPortalViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='cliente.portal@example.com',
            password='segura123',
            name='Cliente Portal',
        )
        self.other_user = get_user_model().objects.create_user(
            email='sem.acesso@example.com',
            password='segura123',
            name='Sem Acesso',
        )
        self.customer = Customer.objects.create(name='Construtora Azul', email='azul@example.com', phone='(11) 9999-9999')
        self.project = Project.objects.create(name='Residencial Azul', customer=self.customer, responsible=self.user)
        self.project_without_data = Project.objects.create(name='Residencial Branco', customer=self.customer, responsible=self.user)
        self.task = ProjectTask.objects.create(
            project=self.project,
            name='Estrutura',
            planned_start_date=date(2026, 5, 1),
            planned_end_date=date(2026, 5, 30),
            planned_percentage=Decimal('60.00'),
            planned_cost=Decimal('60000.00'),
        )
        self.client.force_login(self.user)
        ClientPortalAccess.objects.create(customer=self.customer, user=self.user)
        self.document_visible = CustomerDocument.objects.create(
            customer=self.customer,
            title='Contrato liberado',
            file=SimpleUploadedFile('contrato.pdf', b'%PDF-1.4', content_type='application/pdf'),
            visible_in_portal=True,
        )
        CustomerDocument.objects.create(
            customer=self.customer,
            title='Documento interno',
            file=SimpleUploadedFile('interno.pdf', b'%PDF-1.4', content_type='application/pdf'),
            visible_in_portal=False,
        )
        self.photo_visible = CustomerPhoto.objects.create(
            customer=self.customer,
            title='Foto liberada',
            image=SimpleUploadedFile('foto.png', b'\x89PNG\r\n\x1a\n', content_type='image/png'),
            visible_in_portal=True,
        )
        CustomerPhoto.objects.create(
            customer=self.customer,
            title='Foto interna',
            image=SimpleUploadedFile('interna.png', b'\x89PNG\r\n\x1a\n', content_type='image/png'),
            visible_in_portal=False,
        )
        self.measurement_visible = PhysicalMeasurement.objects.create(
            project=self.project,
            task=self.task,
            measurement_date=date(2026, 5, 5),
            measured_percentage=Decimal('35.00'),
            measured_value=Decimal('21000.00'),
            visible_in_portal=True,
        )
        PhysicalMeasurement.objects.create(
            project=self.project,
            task=self.task,
            measurement_date=date(2026, 5, 6),
            measured_percentage=Decimal('40.00'),
            measured_value=Decimal('24000.00'),
            visible_in_portal=False,
        )

    def test_portal_home_lists_authorized_customers(self):
        response = self.client.get(reverse('client_portal:home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Construtora Azul')
        self.assertContains(response, 'Portal do Cliente')

    def test_customer_portal_shows_basic_data_and_projects(self):
        response = self.client.get(reverse('client_portal:customer_detail', args=[self.customer.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Construtora Azul')
        self.assertContains(response, 'Residencial Azul')
        self.assertContains(response, 'Residencial Branco')

    def test_project_portal_shows_only_visible_information(self):
        response = self.client.get(reverse('client_portal:project_detail', args=[self.customer.pk, self.project.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Residencial Azul')
        self.assertContains(response, 'Contrato liberado')
        self.assertContains(response, 'Foto liberada')
        self.assertContains(response, '35,00%')
        self.assertContains(response, 'Avanço físico consolidado')
        self.assertNotContains(response, 'Documento interno')
        self.assertNotContains(response, 'Foto interna')
        self.assertNotContains(response, '24000,00')
        self.assertNotContains(response, 'Financeiro interno')

    def test_project_portal_shows_empty_state_when_no_visible_items(self):
        response = self.client.get(reverse('client_portal:project_detail', args=[self.customer.pk, self.project_without_data.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nenhuma informação liberada ainda.')

    def test_portal_blocks_users_without_access(self):
        self.client.force_login(self.other_user)

        response = self.client.get(reverse('client_portal:home'))

        self.assertEqual(response.status_code, 403)
