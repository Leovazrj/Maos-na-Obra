from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from budgets.models import InputItem
from core.models import TimeStampedModel
from customers.models import Customer
from projects.models import Project
from purchases.models import PurchaseOrder, PurchaseRequest, PurchaseRequestItem, Quotation, QuotationItemPrice, QuotationSupplier
from suppliers.models import Supplier

from finance.forms import (
    AccountPayableForm,
    AccountReceivableForm,
    FinancialTransactionFilterForm,
    FinancialReceiptBillingForm,
    InvoiceXmlUploadForm,
    FinancialAppropriationForm,
)
from finance.models import AccountPayable, AccountReceivable, FinancialTransaction, FinancialAppropriation, InvoiceXml


class FinanceModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='financeiro@example.com',
            password='segura123',
            name='Financeiro',
        )
        self.customer = Customer.objects.create(name='Cliente Financeiro')
        self.project = Project.objects.create(name='Obra Financeira', customer=self.customer, responsible=self.user)
        self.supplier = Supplier.objects.create(legal_name='Fornecedor Financeiro', email='fornecedor@example.com')
        self.input_item = InputItem.objects.create(name='Cimento', unit='sc', unit_cost=Decimal('45.00'))

    def _create_order(self, unit_price=Decimal('50.00')):
        request = PurchaseRequest.objects.create(project=self.project, title='Solicitação financeira')
        item = PurchaseRequestItem.objects.create(
            purchase_request=request,
            input_item=self.input_item,
            description='Cimento CP II',
            unit='sc',
            quantity=Decimal('2.00'),
        )
        quotation = Quotation.objects.create(purchase_request=request, title='Cotação financeira')
        invited = QuotationSupplier.objects.create(quotation=quotation, supplier=self.supplier)
        QuotationItemPrice.objects.create(
            quotation_supplier=invited,
            purchase_request_item=item,
            unit_price=unit_price,
        )
        return PurchaseOrder.create_from_quotation(quotation)

    def test_models_are_timestamped_and_calculate_open_values(self):
        payable = AccountPayable.objects.create(
            project=self.project,
            supplier=self.supplier,
            title='Conta fornecedor',
            due_date='2026-05-20',
            amount=Decimal('300.00'),
            source_label='Lançamento manual',
        )
        receivable = AccountReceivable.objects.create(
            project=self.project,
            customer=self.customer,
            title='Conta cliente',
            due_date='2026-05-22',
            amount=Decimal('500.00'),
            source_label='Faturamento manual',
        )
        transaction = FinancialTransaction.objects.create(
            project=self.project,
            transaction_type='outflow',
            transaction_date='2026-05-02',
            amount=Decimal('75.00'),
            description='Saída financeira',
        )

        self.assertIsInstance(payable, TimeStampedModel)
        self.assertIsInstance(receivable, TimeStampedModel)
        self.assertIsInstance(transaction, TimeStampedModel)
        self.assertEqual(payable.open_value, Decimal('300.00'))
        self.assertEqual(receivable.open_value, Decimal('500.00'))
        self.assertEqual(transaction.signed_amount, Decimal('-75.00'))
        self.assertEqual(payable.origin_display, 'Lançamento manual')
        self.assertEqual(receivable.origin_display, 'Faturamento manual')

    def test_purchase_order_approval_creates_one_payable(self):
        order = self._create_order()

        order.approve()
        order.refresh_from_db()

        payable = order.account_payable
        self.assertEqual(order.status, 'approved')
        self.assertEqual(payable.amount, Decimal('100.00'))
        self.assertEqual(payable.origin_display, f'Ordem de compra {order.title}')
        self.assertEqual(AccountPayable.objects.filter(purchase_order=order).count(), 1)

    def test_register_payment_creates_transaction_and_marks_paid(self):
        payable = AccountPayable.objects.create(
            project=self.project,
            supplier=self.supplier,
            title='Conta a pagar',
            due_date='2026-05-20',
            amount=Decimal('300.00'),
            source_label='Compra direta',
        )

        transaction = payable.register_payment(transaction_date='2026-05-03', notes='Pagamento realizado')
        payable.refresh_from_db()

        self.assertEqual(payable.status, 'paid')
        self.assertEqual(payable.paid_value, Decimal('300.00'))
        self.assertEqual(transaction.transaction_type, 'outflow')
        self.assertEqual(transaction.amount, Decimal('300.00'))
        self.assertEqual(payable.transactions.count(), 1)

    def test_register_receipt_creates_transaction_and_marks_received(self):
        receivable = AccountReceivable.objects.create(
            project=self.project,
            customer=self.customer,
            title='Conta a receber',
            due_date='2026-05-25',
            amount=Decimal('520.00'),
            source_label='Medição',
        )

        transaction = receivable.register_receipt(transaction_date='2026-05-04', notes='Recebimento realizado')
        receivable.refresh_from_db()

        self.assertEqual(receivable.status, 'received')
        self.assertEqual(receivable.received_value, Decimal('520.00'))
        self.assertEqual(transaction.transaction_type, 'inflow')
        self.assertEqual(transaction.amount, Decimal('520.00'))
        self.assertEqual(receivable.transactions.count(), 1)

    def test_forms_expose_expected_fields(self):
        self.assertIn('project', AccountPayableForm.base_fields)
        self.assertIn('supplier', AccountPayableForm.base_fields)
        self.assertIn('customer', AccountReceivableForm.base_fields)
        self.assertIn('transaction_type', FinancialTransactionFilterForm.base_fields)
        self.assertIn('billing_type', FinancialReceiptBillingForm.base_fields)
        self.assertIn('xml_file', InvoiceXmlUploadForm.base_fields)
        self.assertIn('service_name', FinancialAppropriationForm.base_fields)


class FinanceViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='gestor.financeiro@example.com',
            password='segura123',
            name='Gestor Financeiro',
        )
        self.client.force_login(self.user)
        self.customer = Customer.objects.create(name='Cliente Financeiro')
        self.project = Project.objects.create(name='Obra Caixa', customer=self.customer, responsible=self.user)
        self.supplier = Supplier.objects.create(legal_name='Fornecedor Caixa', email='caixa@example.com')
        self.input_item = InputItem.objects.create(name='Areia', unit='m³', unit_cost=Decimal('80.00'))

    def _create_payable(self):
        return AccountPayable.objects.create(
            project=self.project,
            supplier=self.supplier,
            title='Pagamento de fornecedor',
            due_date='2026-05-18',
            amount=Decimal('400.00'),
            source_label='Compra manual',
        )

    def _create_receivable(self):
        return AccountReceivable.objects.create(
            project=self.project,
            customer=self.customer,
            title='Recebimento de cliente',
            due_date='2026-05-19',
            amount=Decimal('650.00'),
            source_label='Faturamento manual',
        )

    def _pdf_bytes(self, response):
        return b''.join(response.streaming_content)

    def test_payable_list_and_detail_show_origin_and_status(self):
        payable = self._create_payable()

        response = self.client.get(reverse('finance:payable_list'))
        detail = self.client.get(reverse('finance:payable_detail', args=[payable.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Contas a Pagar')
        self.assertContains(detail, 'Pagamento de fornecedor')
        self.assertContains(detail, 'Compra manual')

    def test_payable_payment_view_registers_transaction(self):
        payable = self._create_payable()

        response = self.client.post(reverse('finance:payable_pay', args=[payable.pk]))

        self.assertRedirects(response, reverse('finance:payable_detail', args=[payable.pk]))
        payable.refresh_from_db()
        self.assertEqual(payable.status, 'paid')
        self.assertEqual(payable.transactions.count(), 1)

    def test_receivable_receive_view_registers_transaction(self):
        receivable = self._create_receivable()

        response = self.client.post(reverse('finance:receivable_receive', args=[receivable.pk]))

        self.assertRedirects(response, reverse('finance:receivable_detail', args=[receivable.pk]))
        receivable.refresh_from_db()
        self.assertEqual(receivable.status, 'received')
        self.assertEqual(receivable.transactions.count(), 1)

    def test_transaction_list_shows_cash_flow_totals(self):
        payable = self._create_payable()
        receivable = self._create_receivable()
        payable.register_payment(transaction_date='2026-05-05')
        receivable.register_receipt(transaction_date='2026-05-06')

        response = self.client.get(reverse('finance:transaction_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Fluxo de Caixa')
        self.assertContains(response, 'Entrada realizada')
        self.assertContains(response, 'Saída realizada')
        self.assertContains(response, 'Saldo realizado')

    def test_approved_purchase_order_exposes_payable_link(self):
        request = PurchaseRequest.objects.create(project=self.project, title='Solicitação integrada')
        item = PurchaseRequestItem.objects.create(
            purchase_request=request,
            description='Areia média',
            unit='m³',
            quantity=Decimal('3.00'),
        )
        quotation = Quotation.objects.create(purchase_request=request, title='Cotação integrada')
        invited = QuotationSupplier.objects.create(quotation=quotation, supplier=self.supplier)
        QuotationItemPrice.objects.create(
            quotation_supplier=invited,
            purchase_request_item=item,
            unit_price=Decimal('80.00'),
        )
        order = PurchaseOrder.create_from_quotation(quotation)
        order.approve()

        response = self.client.get(reverse('purchases:order_detail', args=[order.pk]))

        self.assertContains(response, 'Conta a pagar')
        self.assertContains(response, 'Ver conta')
        self.assertContains(response, reverse('finance:payable_detail', args=[order.account_payable.pk]))

    def test_generate_receivable_by_progress_fee(self):
        response = self.client.post(reverse('finance:billing_create'), {
            'project': self.project.pk,
            'billing_type': 'progress_fee',
            'title': 'Taxa por avanço',
            'progress_percentage': '10.00',
            'notes': 'Faturamento mensal',
        })

        receivable = AccountReceivable.objects.get(title='Taxa por avanço')
        self.assertRedirects(response, reverse('finance:receivable_detail', args=[receivable.pk]))
        self.assertEqual(receivable.amount, Decimal('0.00'))
        self.assertEqual(receivable.billing_type, 'progress_fee')
        self.assertEqual(receivable.source_label, 'Taxa por avanço físico')

    def test_invoice_xml_upload_extracts_fields(self):
        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<nfeProc>'
            '<NFe><infNFe Id="NFe35123456789012345678901234567890123456789012">'
            '<emit><xNome>Fornecedor XML Ltda</xNome></emit>'
            '<total><ICMSTot><vNF>1234.56</vNF></ICMSTot></total>'
            '</infNFe></NFe>'
            '</nfeProc>'
        ).encode('utf-8')
        upload = SimpleUploadedFile('nfe.xml', xml, content_type='text/xml')

        response = self.client.post(reverse('finance:invoice_xml_upload'), {
            'project': self.project.pk,
            'xml_file': upload,
        })

        invoice = InvoiceXml.objects.get()
        self.assertRedirects(response, reverse('finance:invoice_xml_detail', args=[invoice.pk]))
        self.assertEqual(invoice.access_key, '35123456789012345678901234567890123456789012')
        self.assertEqual(invoice.issuer_name, 'Fornecedor XML Ltda')
        self.assertEqual(invoice.total_amount, Decimal('1234.56'))
        self.assertIn('nfe', invoice.xml_file.name)

    def test_invoice_appropriation_can_be_created(self):
        invoice = InvoiceXml.objects.create(
            project=self.project,
            xml_file=SimpleUploadedFile('nfe.xml', b'<xml />', content_type='text/xml'),
            access_key='35123456789012345678901234567890123456789012',
            issuer_name='Fornecedor XML Ltda',
            total_amount=Decimal('1234.56'),
        )

        response = self.client.post(reverse('finance:appropriation_create', args=[invoice.pk]), {
            'project': self.project.pk,
            'service_name': 'Fundação',
            'amount': '300.00',
            'percentage': '25.00',
            'notes': 'Apropriação parcial',
        })

        appropriation = FinancialAppropriation.objects.get()
        self.assertRedirects(response, reverse('finance:invoice_xml_detail', args=[invoice.pk]))
        self.assertEqual(appropriation.service_name, 'Fundação')
        self.assertEqual(appropriation.amount, Decimal('300.00'))
        self.assertEqual(appropriation.percentage, Decimal('25.00'))

    def test_invoice_xml_detail_uses_horizontal_action_row(self):
        invoice = InvoiceXml.objects.create(
            project=self.project,
            xml_file=SimpleUploadedFile('nfe.xml', b'<xml />', content_type='text/xml'),
            access_key='35123456789012345678901234567890123456789012',
            issuer_name='Fornecedor XML Ltda',
            total_amount=Decimal('1234.56'),
        )

        response = self.client.get(reverse('finance:invoice_xml_detail', args=[invoice.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'app-action-row')

    def test_project_financial_report_shows_budget_and_balances(self):
        self.client.post(reverse('finance:billing_create'), {
            'project': self.project.pk,
            'billing_type': 'admin',
            'title': 'Administração de obra',
            'amount': '1500.00',
            'notes': 'Taxa administrativa',
        })
        response = self.client.get(reverse('finance:project_report'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Relatório por Obra')
        self.assertContains(response, 'Orçado')
        self.assertContains(response, 'Realizado')
        self.assertContains(response, 'Saldo')

    def test_project_financial_report_pdf_downloads_as_pdf(self):
        response = self.client.get(reverse('finance:project_report_pdf'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(self._pdf_bytes(response).startswith(b'%PDF'))

    def test_transaction_report_pdf_downloads_as_pdf(self):
        response = self.client.get(reverse('finance:transaction_report_pdf'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertTrue(self._pdf_bytes(response).startswith(b'%PDF'))
