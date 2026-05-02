from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, FormView, ListView, UpdateView

from core.views import PostDeleteView
from core.pdf_reports import (
    body,
    build_data_table,
    build_key_value_table,
    build_pdf_response,
    format_currency,
    format_value,
    heading,
    spacer,
    subheading,
)
from projects.models import Project

from .forms import (
    AccountPayableForm,
    AccountReceivableForm,
    FinancialAppropriationForm,
    FinancialReceiptBillingForm,
    FinancialTransactionFilterForm,
    InvoiceXmlUploadForm,
)
from .models import AccountPayable, AccountReceivable, FinancialAppropriation, FinancialTransaction, InvoiceXml
from .services import (
    create_receivable_from_billing,
    parse_invoice_xml,
    summarize_project_financials,
    summarize_transaction_totals,
)


class AccountPayableListView(LoginRequiredMixin, ListView):
    model = AccountPayable
    template_name = 'finance/payable_list.html'
    context_object_name = 'payables'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('project', 'supplier', 'purchase_order')
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(project__name__icontains=search)
                | Q(supplier__legal_name__icontains=search)
                | Q(source_label__icontains=search)
            )
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['open_total'] = self.get_queryset().filter(status='open').aggregate(total=Sum('amount'))['total'] or 0
        context['paid_total'] = self.get_queryset().filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
        return context


class AccountPayableCreateView(LoginRequiredMixin, CreateView):
    model = AccountPayable
    form_class = AccountPayableForm
    template_name = 'finance/payable_form.html'
    success_url = reverse_lazy('finance:payable_list')

    def form_valid(self, form):
        messages.success(self.request, 'Conta a pagar cadastrada com sucesso.')
        return super().form_valid(form)


class AccountPayableUpdateView(LoginRequiredMixin, UpdateView):
    model = AccountPayable
    form_class = AccountPayableForm
    template_name = 'finance/payable_form.html'

    def get_success_url(self):
        return reverse('finance:payable_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Conta a pagar atualizada com sucesso.')
        return super().form_valid(form)


class AccountPayableDeleteView(PostDeleteView):
    model = AccountPayable
    success_url = reverse_lazy('finance:payable_list')
    success_message = 'Conta a pagar excluída com sucesso.'


class AccountPayableDetailView(LoginRequiredMixin, DetailView):
    model = AccountPayable
    template_name = 'finance/payable_detail.html'
    context_object_name = 'payable'
    queryset = AccountPayable.objects.select_related('project', 'supplier', 'purchase_order').prefetch_related('transactions')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transactions'] = self.object.transactions.all()
        return context


class AccountPayablePaymentView(LoginRequiredMixin, View):
    def post(self, request, pk):
        payable = get_object_or_404(AccountPayable, pk=pk)
        try:
            payable.register_payment()
            messages.success(request, 'Pagamento registrado com sucesso.')
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect('finance:payable_detail', pk=payable.pk)


class AccountReceivableListView(LoginRequiredMixin, ListView):
    model = AccountReceivable
    template_name = 'finance/receivable_list.html'
    context_object_name = 'receivables'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('project', 'customer')
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(project__name__icontains=search)
                | Q(customer__name__icontains=search)
                | Q(source_label__icontains=search)
            )
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['open_total'] = self.get_queryset().filter(status='open').aggregate(total=Sum('amount'))['total'] or 0
        context['received_total'] = self.get_queryset().filter(status='received').aggregate(total=Sum('amount'))['total'] or 0
        return context


class AccountReceivableCreateView(LoginRequiredMixin, CreateView):
    model = AccountReceivable
    form_class = AccountReceivableForm
    template_name = 'finance/receivable_form.html'
    success_url = reverse_lazy('finance:receivable_list')

    def form_valid(self, form):
        messages.success(self.request, 'Conta a receber cadastrada com sucesso.')
        return super().form_valid(form)


class AccountReceivableUpdateView(LoginRequiredMixin, UpdateView):
    model = AccountReceivable
    form_class = AccountReceivableForm
    template_name = 'finance/receivable_form.html'

    def get_success_url(self):
        return reverse('finance:receivable_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Conta a receber atualizada com sucesso.')
        return super().form_valid(form)


class AccountReceivableDeleteView(PostDeleteView):
    model = AccountReceivable
    success_url = reverse_lazy('finance:receivable_list')
    success_message = 'Conta a receber excluída com sucesso.'


class AccountReceivableDetailView(LoginRequiredMixin, DetailView):
    model = AccountReceivable
    template_name = 'finance/receivable_detail.html'
    context_object_name = 'receivable'
    queryset = AccountReceivable.objects.select_related('project', 'customer').prefetch_related('transactions')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transactions'] = self.object.transactions.all()
        return context


class AccountReceivableReceiveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        receivable = get_object_or_404(AccountReceivable, pk=pk)
        try:
            receivable.register_receipt()
            messages.success(request, 'Recebimento registrado com sucesso.')
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect('finance:receivable_detail', pk=receivable.pk)


class FinancialBillingCreateView(LoginRequiredMixin, FormView):
    form_class = FinancialReceiptBillingForm
    template_name = 'finance/billing_form.html'

    def form_valid(self, form):
        data = form.cleaned_data
        receivable = create_receivable_from_billing(
            project=data['project'],
            billing_type=data['billing_type'],
            title=data['title'],
            amount=data.get('amount'),
            measurement=data.get('measurement'),
            progress_percentage=data.get('progress_percentage'),
            notes=data.get('notes', ''),
        )
        messages.success(self.request, 'Faturamento gerado com sucesso.')
        return redirect('finance:receivable_detail', pk=receivable.pk)


class InvoiceXmlUploadView(LoginRequiredMixin, FormView):
    form_class = InvoiceXmlUploadForm
    template_name = 'finance/invoice_xml_form.html'

    def form_valid(self, form):
        uploaded_file = self.request.FILES['xml_file']
        parsed = parse_invoice_xml(uploaded_file)
        invoice = InvoiceXml.objects.create(
            project=form.cleaned_data['project'],
            xml_file=uploaded_file,
            access_key=parsed['access_key'],
            issuer_name=parsed['issuer_name'],
            total_amount=parsed['total_amount'],
        )
        messages.success(self.request, 'XML importado com sucesso.')
        return redirect('finance:invoice_xml_detail', pk=invoice.pk)


class InvoiceXmlDetailView(LoginRequiredMixin, DetailView):
    model = InvoiceXml
    template_name = 'finance/invoice_xml_detail.html'
    context_object_name = 'invoice'
    queryset = InvoiceXml.objects.select_related('project').prefetch_related('appropriations')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['appropriation_form'] = FinancialAppropriationForm(initial={'project': self.object.project})
        context['appropriations'] = self.object.appropriations.select_related('project')
        return context


class FinancialAppropriationCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        invoice = get_object_or_404(InvoiceXml, pk=pk)
        form = FinancialAppropriationForm(request.POST)
        if form.is_valid():
            appropriation = form.save(commit=False)
            appropriation.invoice_xml = invoice
            appropriation.project = invoice.project
            appropriation.save()
            messages.success(request, 'Apropriação registrada com sucesso.')
        else:
            messages.error(request, 'Não foi possível registrar a apropriação.')
        return redirect('finance:invoice_xml_detail', pk=invoice.pk)


class InvoiceXmlDeleteView(PostDeleteView):
    model = InvoiceXml
    success_url = reverse_lazy('finance:transaction_list')
    success_message = 'NFe XML excluída com sucesso.'


class FinancialAppropriationDeleteView(PostDeleteView):
    model = FinancialAppropriation
    success_url = reverse_lazy('finance:transaction_list')
    success_message = 'Apropriação excluída com sucesso.'

    def get_success_url(self):
        if self.object and self.object.invoice_xml_id:
            return reverse('finance:invoice_xml_detail', kwargs={'pk': self.object.invoice_xml_id})
        return super().get_success_url()


class ProjectFinancialReportView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'finance/project_report.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return super().get_queryset().select_related('customer').prefetch_related('budgets', 'financial_transactions', 'accounts_payable', 'accounts_receivable', 'financial_appropriations')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = []
        totals = {
            'budget_total': 0,
            'realized_cost': 0,
            'balance': 0,
            'open_payables': 0,
            'open_receivables': 0,
        }
        for project in self.get_queryset():
            summary = summarize_project_financials(project)
            totals['budget_total'] += summary['budget_total']
            totals['realized_cost'] += summary['realized_cost']
            totals['balance'] += summary['balance']
            totals['open_payables'] += summary['open_payables']
            totals['open_receivables'] += summary['open_receivables']
            rows.append({
                'project': project,
                **summary,
            })
        context['rows'] = rows
        context['totals'] = totals
        return context


class ProjectFinancialReportPdfView(LoginRequiredMixin, View):
    def get(self, request):
        projects = Project.objects.select_related('customer').prefetch_related(
            'budgets',
            'financial_transactions',
            'accounts_payable',
            'accounts_receivable',
            'financial_appropriations',
        )
        rows = []
        for project in projects:
            summary = summarize_project_financials(project)
            rows.append([
                project.name,
                format_currency(summary['budget_total']),
                format_currency(summary['realized_cost']),
                format_currency(summary['balance']),
                format_currency(summary['open_payables']),
                format_currency(summary['open_receivables']),
            ])

        story = [
            heading('Relatório financeiro por obra'),
            body('Visão consolidada das obras cadastradas com orçamento, custo realizado e saldos em aberto.'),
            spacer(8),
            build_data_table(
                ['Obra', 'Orçado', 'Realizado', 'Saldo', 'Pagar', 'Receber'],
                rows,
                col_widths=[60 * 1, 20 * 10, 20 * 10, 20 * 10, 20 * 10, 20 * 10],
            ),
        ]
        return build_pdf_response('relatorio-financeiro-obras.pdf', 'Relatório financeiro por obra', story)


class FinancialTransactionListView(LoginRequiredMixin, ListView):
    model = FinancialTransaction
    template_name = 'finance/transaction_list.html'
    context_object_name = 'transactions'

    def get_filter_form(self):
        return FinancialTransactionFilterForm(self.request.GET or None)

    def get_queryset(self):
        queryset = super().get_queryset().select_related('project', 'account_payable', 'account_receivable')
        form = self.get_filter_form()
        if form.is_valid():
            project = form.cleaned_data.get('project')
            transaction_type = form.cleaned_data.get('transaction_type')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            if project:
                queryset = queryset.filter(project=project)
            if transaction_type:
                queryset = queryset.filter(transaction_type=transaction_type)
            if date_from:
                queryset = queryset.filter(transaction_date__gte=date_from)
            if date_to:
                queryset = queryset.filter(transaction_date__lte=date_to)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = self.get_filter_form()
        transactions = self.get_queryset()
        totals = summarize_transaction_totals(transactions)
        context['filter_form'] = form
        context['cash_in_total'] = totals['inflow']
        context['cash_out_total'] = totals['outflow']
        context['balance_total'] = totals['balance']
        context['open_payables_total'] = AccountPayable.objects.filter(status='open').aggregate(total=Sum('amount'))['total'] or 0
        context['open_receivables_total'] = AccountReceivable.objects.filter(status='open').aggregate(total=Sum('amount'))['total'] or 0
        context['pending_balance'] = context['open_receivables_total'] - context['open_payables_total']
        return context


class FinancialTransactionPdfView(LoginRequiredMixin, View):
    def get(self, request):
        view = FinancialTransactionListView()
        view.request = request
        transactions = view.get_queryset()
        totals = summarize_transaction_totals(transactions)
        rows = []
        for transaction in transactions.select_related('project').order_by('-transaction_date', '-created_at'):
            rows.append([
                format_value(transaction.transaction_date),
                transaction.description,
                transaction.project.name if transaction.project else '-',
                transaction.get_transaction_type_display(),
                format_currency(transaction.amount),
            ])

        story = [
            heading('Fluxo de caixa'),
            body('Resumo das movimentações financeiras com filtro aplicado na tela atual.'),
            spacer(8),
            build_key_value_table([
                ('Entrada realizada', format_currency(totals['inflow'])),
                ('Saída realizada', format_currency(totals['outflow'])),
                ('Saldo realizado', format_currency(totals['balance'])),
                ('Entrada prevista', format_currency(AccountReceivable.objects.filter(status='open').aggregate(total=Sum('amount'))['total'] or 0)),
                ('Saída prevista', format_currency(AccountPayable.objects.filter(status='open').aggregate(total=Sum('amount'))['total'] or 0)),
                ('Saldo previsto', format_currency((AccountReceivable.objects.filter(status='open').aggregate(total=Sum('amount'))['total'] or 0) - (AccountPayable.objects.filter(status='open').aggregate(total=Sum('amount'))['total'] or 0))),
            ]),
            spacer(8),
            subheading('Movimentações'),
            build_data_table(['Data', 'Descrição', 'Obra', 'Tipo', 'Valor'], rows, col_widths=[22 * 10, 55 * 10, 45 * 10, 28 * 10, 25 * 10]),
        ]
        return build_pdf_response('fluxo-de-caixa.pdf', 'Fluxo de caixa', story)


class FinancialTransactionDeleteView(PostDeleteView):
    model = FinancialTransaction
    success_url = reverse_lazy('finance:transaction_list')
    success_message = 'Movimentação financeira excluída com sucesso.'
