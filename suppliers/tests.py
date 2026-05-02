from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from core.models import TimeStampedModel
from suppliers.forms import SupplierForm
from suppliers.models import Supplier, SupplierCategory


class SupplierModelTests(TestCase):
    def test_supplier_and_category_are_timestamped_and_related(self):
        category = SupplierCategory.objects.create(name='Materiais elétricos')
        supplier = Supplier.objects.create(
            legal_name='Eletro Forte Ltda',
            trade_name='Eletro Forte',
            document_number='12.345.678/0001-90',
            email='compras@eletroforte.com.br',
            phone='11999990000',
            address='Rua das Obras, 100',
            notes='Entrega em até dois dias.',
        )
        supplier.categories.add(category)

        self.assertIsInstance(category, TimeStampedModel)
        self.assertIsInstance(supplier, TimeStampedModel)
        self.assertEqual(str(category), 'Materiais elétricos')
        self.assertEqual(str(supplier), 'Eletro Forte Ltda')
        self.assertEqual(list(supplier.categories.all()), [category])

    def test_active_supplier_requires_email(self):
        form = SupplierForm(data={
            'legal_name': 'Sem Email Ltda',
            'trade_name': '',
            'document_number': '',
            'email': '',
            'phone': '',
            'address': '',
            'categories': [],
            'notes': '',
            'status': 'active',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_active_supplier_model_validation_requires_email(self):
        supplier = Supplier(legal_name='Sem Email Ltda', status='active')

        with self.assertRaises(ValidationError):
            supplier.full_clean()


class SupplierViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='gestor@example.com',
            password='segura123',
            name='Gestor da Obra',
        )
        self.client.force_login(self.user)
        self.electric = SupplierCategory.objects.create(name='Elétrica')
        self.plumbing = SupplierCategory.objects.create(name='Hidráulica')
        self.active_supplier = Supplier.objects.create(
            legal_name='Elétrica Central',
            email='contato@eletricacentral.com.br',
        )
        self.active_supplier.categories.add(self.electric)
        self.no_email_supplier = Supplier.objects.create(
            legal_name='Hidráulica Sem Email',
            status='inactive',
        )
        self.no_email_supplier.categories.add(self.plumbing)

    def test_list_filters_suppliers_by_category_and_shows_quote_selection_state(self):
        response = self.client.get(reverse('suppliers:list'), {'category': self.electric.pk})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Elétrica Central')
        self.assertNotContains(response, 'Hidráulica Sem Email')
        self.assertContains(response, 'Selecionar para cotação')

    def test_detail_shows_supplier_categories_and_missing_email_empty_state(self):
        response = self.client.get(reverse('suppliers:detail', args=[self.no_email_supplier.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Hidráulica')
        self.assertContains(response, 'Fornecedor sem email cadastrado')

    def test_inactivate_action_changes_supplier_status(self):
        response = self.client.post(reverse('suppliers:inactivate', args=[self.active_supplier.pk]))

        self.assertRedirects(response, reverse('suppliers:detail', args=[self.active_supplier.pk]))
        self.active_supplier.refresh_from_db()
        self.assertEqual(self.active_supplier.status, 'inactive')
