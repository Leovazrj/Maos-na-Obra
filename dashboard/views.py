from decimal import Decimal

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.views.generic import TemplateView

from finance.models import AccountPayable, AccountReceivable, FinancialTransaction
from projects.models import Project
from purchases.models import PurchaseRequest, PurchaseOrder, Quotation


def format_brl(value):
    amount = (value or Decimal('0.00')).quantize(Decimal('0.01'))
    formatted = f'{amount:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f'R$ {formatted}'


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        open_payables_total = AccountPayable.objects.filter(status='open').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        open_receivables_total = AccountReceivable.objects.filter(status='open').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        financial_balance_total = Decimal('0.00')
        for transaction_type, amount in FinancialTransaction.objects.values_list('transaction_type', 'amount'):
            financial_balance_total += amount if transaction_type == 'inflow' else -amount

        latest_transactions = []
        for transaction in FinancialTransaction.objects.select_related('project').order_by('-transaction_date', '-created_at')[:5]:
            latest_transactions.append({
                'transaction': transaction,
                'amount_display': format_brl(transaction.amount),
                'badge_class': 'text-success' if transaction.transaction_type == 'inflow' else 'text-danger',
                'direction_label': transaction.get_transaction_type_display(),
                'project_name': transaction.project.name if transaction.project else 'Movimentação geral',
            })

        cash_flow_rows = (
            FinancialTransaction.objects.values('transaction_date')
            .annotate(
                inflow=Sum('amount', filter=Q(transaction_type='inflow')),
                outflow=Sum('amount', filter=Q(transaction_type='outflow')),
            )
            .order_by('transaction_date')
        )
        cash_flow_labels = []
        cash_flow_inflows = []
        cash_flow_outflows = []
        for row in cash_flow_rows:
            cash_flow_labels.append(row['transaction_date'].strftime('%d/%m'))
            cash_flow_inflows.append(float(row['inflow'] or 0))
            cash_flow_outflows.append(float(row['outflow'] or 0))

        if not cash_flow_labels:
            cash_flow_labels = ['Sem dados']
            cash_flow_inflows = [0]
            cash_flow_outflows = [0]

        purchase_pipeline_labels = ['Solicitações abertas', 'Cotações em aberto', 'Ordens em rascunho', 'Ordens aprovadas']
        purchase_pipeline_series = [
            PurchaseRequest.objects.exclude(status__in=['ordered', 'cancelled']).count(),
            Quotation.objects.filter(status='open').count(),
            PurchaseOrder.objects.filter(status='draft').count(),
            PurchaseOrder.objects.filter(status='approved').count(),
        ]
        if not any(purchase_pipeline_series):
            purchase_pipeline_labels = ['Sem dados']
            purchase_pipeline_series = [1]

        context['active_projects_count'] = Project.objects.filter(status='active').count()
        context['open_payables_total'] = open_payables_total
        context['open_payables_total_display'] = format_brl(open_payables_total)
        context['open_receivables_total'] = open_receivables_total
        context['open_receivables_total_display'] = format_brl(open_receivables_total)
        context['financial_balance_total'] = financial_balance_total
        context['financial_balance_total_display'] = format_brl(financial_balance_total)
        context['pending_quotations_count'] = Quotation.objects.filter(status='open').count()
        context['pending_purchase_orders_count'] = PurchaseRequest.objects.exclude(status__in=['ordered', 'cancelled']).count()
        context['latest_transactions'] = latest_transactions
        context['cash_flow_chart_labels'] = cash_flow_labels
        context['cash_flow_chart_inflows'] = cash_flow_inflows
        context['cash_flow_chart_outflows'] = cash_flow_outflows
        context['purchase_pipeline_labels'] = purchase_pipeline_labels
        context['purchase_pipeline_series'] = purchase_pipeline_series
        return context
