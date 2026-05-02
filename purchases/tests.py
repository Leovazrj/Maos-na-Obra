from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from budgets.models import InputItem
from core.models import TimeStampedModel
from customers.models import Customer
from projects.models import Project
from suppliers.models import Supplier
from purchases.forms import PurchaseRequestForm, PurchaseRequestItemForm, QuotationItemPriceForm, QuotationSupplierForm
from purchases.models import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequest,
    PurchaseRequestItem,
    Quotation,
    QuotationItemPrice,
    QuotationSupplier,
)


class PurchaseModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='compras@example.com',
            password='segura123',
            name='Compras',
        )
        self.customer = Customer.objects.create(name='Cliente Compras')
        self.project = Project.objects.create(name='Obra Compras', customer=self.customer, responsible=self.user)
        self.supplier_a = Supplier.objects.create(legal_name='Fornecedor A', email='a@example.com')
        self.supplier_b = Supplier.objects.create(legal_name='Fornecedor B', email='b@example.com')
        self.input_item = InputItem.objects.create(name='Tijolo', unit='un', unit_cost=Decimal('2.50'))

    def test_request_quotation_and_order_models_are_timestamped(self):
        request = PurchaseRequest.objects.create(project=self.project, title='Solicitação 01')
        item = PurchaseRequestItem.objects.create(
            purchase_request=request,
            input_item=self.input_item,
            description='Tijolo baiano',
            unit='un',
            quantity=Decimal('100.00'),
        )
        quotation = Quotation.objects.create(purchase_request=request, title='Cotação 01')
        invited_a = QuotationSupplier.objects.create(quotation=quotation, supplier=self.supplier_a)
        invited_b = QuotationSupplier.objects.create(quotation=quotation, supplier=self.supplier_b)
        QuotationItemPrice.objects.create(
            quotation_supplier=invited_a,
            purchase_request_item=item,
            unit_price=Decimal('2.00'),
        )
        QuotationItemPrice.objects.create(
            quotation_supplier=invited_b,
            purchase_request_item=item,
            unit_price=Decimal('2.50'),
        )
        order = PurchaseOrder.objects.create(purchase_request=request, quotation=quotation, supplier=self.supplier_a, title='OC 01')
        order_item = PurchaseOrderItem.objects.create(
            purchase_order=order,
            purchase_request_item=item,
            description='Tijolo baiano',
            unit='un',
            quantity=Decimal('100.00'),
            unit_price=Decimal('2.00'),
        )

        self.assertIsInstance(request, TimeStampedModel)
        self.assertIsInstance(item, TimeStampedModel)
        self.assertIsInstance(quotation, TimeStampedModel)
        self.assertIsInstance(order, TimeStampedModel)
        self.assertEqual(request.total_items, 1)
        self.assertEqual(quotation.total_suppliers, 2)
        self.assertEqual(quotation.total_value, Decimal('200.00'))
        self.assertEqual(order.total_value, Decimal('200.00'))
        self.assertEqual(order_item.total_price, Decimal('200.00'))

    def test_purchase_request_form_exposes_project(self):
        self.assertIn('project', PurchaseRequestForm.base_fields)
        self.assertIn('input_item', PurchaseRequestItemForm.base_fields)
        self.assertIn('supplier', QuotationSupplierForm.base_fields)
        self.assertIn('unit_price', QuotationItemPriceForm.base_fields)


class PurchaseViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='gestor@example.com',
            password='segura123',
            name='Gestor',
        )
        self.client.force_login(self.user)
        self.customer = Customer.objects.create(name='Cliente Vendas')
        self.project = Project.objects.create(name='Obra Vendas', customer=self.customer, responsible=self.user)
        self.supplier_a = Supplier.objects.create(legal_name='Fornecedor Alpha', email='alpha@example.com')
        self.supplier_b = Supplier.objects.create(legal_name='Fornecedor Beta', email='beta@example.com')
        self.request = PurchaseRequest.objects.create(project=self.project, title='Pedido de compra')
        self.item = PurchaseRequestItem.objects.create(
            purchase_request=self.request,
            description='Cimento CP II',
            unit='sc',
            quantity=Decimal('10.00'),
        )

    def test_request_detail_shows_items_and_buttons(self):
        response = self.client.get(reverse('purchases:request_detail', args=[self.request.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pedido de compra')
        self.assertContains(response, 'Cimento CP II')
        self.assertContains(response, 'Gerar cotação')

    def test_generate_quotation_creates_invited_suppliers(self):
        response = self.client.post(reverse('purchases:quotation_generate', args=[self.request.pk]), {
            'suppliers': [self.supplier_a.pk, self.supplier_b.pk],
        })

        quotation = Quotation.objects.get(purchase_request=self.request)
        self.assertRedirects(response, reverse('purchases:quotation_detail', args=[quotation.pk]))
        self.assertEqual(quotation.suppliers.count(), 2)

    def test_quote_map_highlights_winner_and_best_total(self):
        quotation = Quotation.objects.create(purchase_request=self.request, title='Cotação mapa')
        invited_a = QuotationSupplier.objects.create(quotation=quotation, supplier=self.supplier_a)
        invited_b = QuotationSupplier.objects.create(quotation=quotation, supplier=self.supplier_b)
        QuotationItemPrice.objects.create(quotation_supplier=invited_a, purchase_request_item=self.item, unit_price=Decimal('9.00'))
        QuotationItemPrice.objects.create(quotation_supplier=invited_b, purchase_request_item=self.item, unit_price=Decimal('8.00'))

        response = self.client.get(reverse('purchases:quotation_detail', args=[quotation.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mapa de cotação')
        self.assertContains(response, 'Fornecedor Beta')
        self.assertContains(response, 'Menor preço')

    def test_quotation_detail_uses_horizontal_action_row(self):
        quotation = Quotation.objects.create(purchase_request=self.request, title='Cotação mapa')

        response = self.client.get(reverse('purchases:quotation_detail', args=[quotation.pk]))

        self.assertContains(response, 'app-action-row')
        self.assertContains(response, 'btn-light-brand')
        self.assertNotContains(response, 'btn-danger')

    def test_generate_purchase_order_copies_winner_prices(self):
        quotation = Quotation.objects.create(purchase_request=self.request, title='Cotação finalizada', status='finished')
        invited_a = QuotationSupplier.objects.create(quotation=quotation, supplier=self.supplier_a)
        QuotationItemPrice.objects.create(quotation_supplier=invited_a, purchase_request_item=self.item, unit_price=Decimal('7.50'))

        response = self.client.post(reverse('purchases:purchase_order_generate', args=[quotation.pk]))

        order = PurchaseOrder.objects.get(quotation=quotation)
        self.assertRedirects(response, reverse('purchases:order_detail', args=[order.pk]))
        self.assertEqual(order.total_value, Decimal('75.00'))
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.status, 'draft')

    def test_finalize_quotation_rejects_missing_item_prices(self):
        quotation = Quotation.objects.create(purchase_request=self.request, title='Cotação em aberto')
        QuotationSupplier.objects.create(quotation=quotation, supplier=self.supplier_a)

        response = self.client.post(reverse('purchases:quotation_finalize', args=[quotation.pk]))

        self.assertRedirects(response, reverse('purchases:quotation_detail', args=[quotation.pk]))
        quotation.refresh_from_db()
        self.assertEqual(quotation.status, 'open')

    def test_approve_purchase_order_changes_status(self):
        quotation = Quotation.objects.create(purchase_request=self.request, title='Cotação aprovada')
        order = PurchaseOrder.objects.create(
            purchase_request=self.request,
            quotation=quotation,
            title='OC',
            supplier=self.supplier_a,
        )

        response = self.client.post(reverse('purchases:order_approve', args=[order.pk]))

        self.assertRedirects(response, reverse('purchases:order_detail', args=[order.pk]))
        order.refresh_from_db()
        self.assertEqual(order.status, 'approved')

    def test_purchase_request_create_view_persists_request_and_redirects(self):
        response = self.client.post(reverse('purchases:request_create'), {
            'project': self.project.pk,
            'title': 'Solicitação nova',
            'status': 'draft',
            'notes': 'Criação via teste',
        })

        request = PurchaseRequest.objects.get(title='Solicitação nova')
        self.assertRedirects(response, reverse('purchases:request_list'))
        self.assertEqual(request.project, self.project)

    def test_request_report_pdf_downloads_as_pdf(self):
        response = self.client.get(reverse('purchases:request_report_pdf', args=[self.request.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF'))

    def test_quotation_report_pdf_downloads_as_pdf(self):
        quotation = Quotation.objects.create(purchase_request=self.request, title='Cotação PDF')
        invited = QuotationSupplier.objects.create(quotation=quotation, supplier=self.supplier_a)
        QuotationItemPrice.objects.create(
            quotation_supplier=invited,
            purchase_request_item=self.item,
            unit_price=Decimal('9.50'),
        )

        response = self.client.get(reverse('purchases:quotation_report_pdf', args=[quotation.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF'))

    def test_order_report_pdf_downloads_as_pdf(self):
        quotation = Quotation.objects.create(purchase_request=self.request, title='Cotação PDF')
        invited = QuotationSupplier.objects.create(quotation=quotation, supplier=self.supplier_a)
        QuotationItemPrice.objects.create(
            quotation_supplier=invited,
            purchase_request_item=self.item,
            unit_price=Decimal('9.50'),
        )
        order = PurchaseOrder.create_from_quotation(quotation)

        response = self.client.get(reverse('purchases:order_report_pdf', args=[order.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF'))
