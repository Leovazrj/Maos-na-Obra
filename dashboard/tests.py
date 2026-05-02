from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from customers.models import Customer
from finance.models import AccountPayable, AccountReceivable, FinancialTransaction
from projects.models import Project
from purchases.models import PurchaseOrder, PurchaseRequest, Quotation
from suppliers.models import Supplier


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
        self.assertContains(response, 'id="profileDropdownToggle"')
        self.assertContains(response, 'id="profileDropdownMenu"')
        self.assertContains(response, 'app-profile-dropdown')


class DashboardDataTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='gestor.dashboard@example.com',
            password='segura123',
            name='Gestor Dashboard',
        )
        self.client.force_login(self.user)
        self.customer = Customer.objects.create(name='Cliente Dashboard')
        self.project_active = Project.objects.create(
            name='Obra Ativa',
            customer=self.customer,
            responsible=self.user,
            status='active',
        )
        self.project_inactive = Project.objects.create(
            name='Obra Inativa',
            customer=self.customer,
            responsible=self.user,
            status='closed',
        )
        self.supplier = Supplier.objects.create(legal_name='Fornecedor Dashboard', email='fornecedor@dashboard.com')

    def test_dashboard_shows_live_summary_values(self):
        payable = AccountPayable.objects.create(
            project=self.project_active,
            supplier=self.supplier,
            title='Conta a pagar dashboard',
            due_date='2026-05-12',
            amount=Decimal('250.00'),
            source_label='Compra dashboard',
        )
        receivable = AccountReceivable.objects.create(
            project=self.project_active,
            customer=self.customer,
            title='Conta a receber dashboard',
            due_date='2026-05-13',
            amount=Decimal('480.00'),
            source_label='Faturamento dashboard',
        )
        FinancialTransaction.objects.create(
            project=self.project_active,
            transaction_type='outflow',
            transaction_date='2026-05-11',
            amount=Decimal('120.00'),
            description='Saída dashboard',
        )
        FinancialTransaction.objects.create(
            project=self.project_active,
            transaction_type='inflow',
            transaction_date='2026-05-11',
            amount=Decimal('500.00'),
            description='Entrada dashboard',
        )
        request = PurchaseRequest.objects.create(project=self.project_active, title='Solicitação dashboard')
        quotation_open = Quotation.objects.create(purchase_request=request, title='Cotação dashboard aberta')
        quotation_finished = Quotation.objects.create(
            purchase_request=request,
            title='Cotação dashboard finalizada',
            status='finished',
        )
        PurchaseOrder.objects.create(
            purchase_request=request,
            quotation=quotation_finished,
            supplier=self.supplier,
            title='OC dashboard',
            status='draft',
        )

        response = self.client.get(reverse('dashboard:home'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_projects_count'], 1)
        self.assertEqual(response.context['open_payables_total'], Decimal('250.00'))
        self.assertEqual(response.context['open_receivables_total'], Decimal('480.00'))
        self.assertEqual(response.context['financial_balance_total'], Decimal('380.00'))
        self.assertEqual(response.context['pending_quotations_count'], 1)
        self.assertEqual(response.context['pending_purchase_orders_count'], 1)
        self.assertContains(response, 'Obra Ativa')
        self.assertContains(response, 'R$ 250,00')
        self.assertContains(response, 'R$ 480,00')
        self.assertContains(response, 'R$ 380,00')
        self.assertContains(response, 'Entrada dashboard')
        self.assertContains(response, 'Saída dashboard')

    def test_dashboard_counts_purchase_requests_waiting_approval(self):
        PurchaseRequest.objects.create(
            project=self.project_active,
            title='Solicitação em aberto',
            status='open',
        )
        PurchaseRequest.objects.create(
            project=self.project_active,
            title='Solicitação cotada',
            status='quoted',
        )
        PurchaseRequest.objects.create(
            project=self.project_active,
            title='Solicitação ordenada',
            status='ordered',
        )

        response = self.client.get(reverse('dashboard:home'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['pending_purchase_orders_count'], 2)
