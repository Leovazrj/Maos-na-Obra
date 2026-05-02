from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.views import PostDeleteView
from budgets.models import InputItem
from suppliers.models import Supplier

from .forms import PurchaseRequestForm, PurchaseRequestItemForm, QuotationForm, QuotationItemPriceForm, QuotationSupplierForm
from .models import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequest,
    PurchaseRequestItem,
    Quotation,
    QuotationItemPrice,
    QuotationSupplier,
)


class PurchaseRequestListView(LoginRequiredMixin, ListView):
    model = PurchaseRequest
    template_name = 'purchases/request_list.html'
    context_object_name = 'requests'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('project')
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        if search:
            queryset = queryset.filter(Q(title__icontains=search) | Q(project__name__icontains=search))
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        return context


class PurchaseRequestCreateView(LoginRequiredMixin, CreateView):
    model = PurchaseRequest
    form_class = PurchaseRequestForm
    template_name = 'purchases/request_form.html'
    success_url = reverse_lazy('purchases:request_list')

    def form_valid(self, form):
        messages.success(self.request, 'Solicitação de compra cadastrada com sucesso!')
        return super().form_valid(form)


class PurchaseRequestUpdateView(LoginRequiredMixin, UpdateView):
    model = PurchaseRequest
    form_class = PurchaseRequestForm
    template_name = 'purchases/request_form.html'

    def get_success_url(self):
        return reverse('purchases:request_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Solicitação de compra atualizada com sucesso!')
        return super().form_valid(form)


class PurchaseRequestDeleteView(PostDeleteView):
    model = PurchaseRequest
    success_url = reverse_lazy('purchases:request_list')
    success_message = 'Solicitação de compra excluída com sucesso.'


class PurchaseRequestDetailView(LoginRequiredMixin, DetailView):
    model = PurchaseRequest
    template_name = 'purchases/request_detail.html'
    context_object_name = 'purchase_request'
    queryset = PurchaseRequest.objects.select_related('project').prefetch_related('items', 'quotations__suppliers')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item_form = PurchaseRequestItemForm()
        item_form.fields['input_item'].queryset = InputItem.objects.filter(is_active=True)
        context['item_form'] = item_form
        context['suppliers'] = Supplier.objects.filter(status='active').order_by('legal_name')
        context['quotation_form'] = QuotationForm()
        context['quotations'] = self.object.quotations.select_related('winner_supplier').prefetch_related('suppliers__supplier')
        return context


class PurchaseRequestItemCreateView(LoginRequiredMixin, View):
    def post(self, request, request_id):
        purchase_request = get_object_or_404(PurchaseRequest, pk=request_id)
        form = PurchaseRequestItemForm(request.POST)
        form.fields['input_item'].queryset = InputItem.objects.filter(is_active=True)
        if form.is_valid():
            item = form.save(commit=False)
            item.purchase_request = purchase_request
            item.save()
            messages.success(request, 'Item adicionado à solicitação.')
        else:
            messages.error(request, 'Não foi possível adicionar o item.')
        return redirect('purchases:request_detail', pk=purchase_request.pk)


class PurchaseRequestItemDeleteView(LoginRequiredMixin, View):
    def post(self, request, request_id, pk):
        purchase_request = get_object_or_404(PurchaseRequest, pk=request_id)
        item = get_object_or_404(PurchaseRequestItem, pk=pk, purchase_request=purchase_request)
        item.delete()
        messages.success(request, 'Item removido da solicitação.')
        return redirect('purchases:request_detail', pk=purchase_request.pk)


class QuotationGenerateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        purchase_request = get_object_or_404(PurchaseRequest, pk=pk)
        quotation = Quotation.objects.create(
            purchase_request=purchase_request,
            title=f'Cotação - {purchase_request.title}',
            status='open',
        )
        supplier_ids = request.POST.getlist('suppliers')
        suppliers = Supplier.objects.filter(pk__in=supplier_ids, status='active')
        for supplier in suppliers:
            QuotationSupplier.objects.get_or_create(quotation=quotation, supplier=supplier)
        purchase_request.open_quotation()
        messages.success(request, 'Cotação gerada com sucesso.')
        return redirect('purchases:quotation_detail', pk=quotation.pk)


class QuotationDetailView(LoginRequiredMixin, DetailView):
    model = Quotation
    template_name = 'purchases/quotation_detail.html'
    context_object_name = 'quotation'
    queryset = Quotation.objects.select_related('purchase_request', 'winner_supplier').prefetch_related(
        'purchase_request__items',
        'suppliers__supplier',
        'suppliers__item_prices__purchase_request_item',
    )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request_items = list(self.object.purchase_request.items.all())
        quotation_suppliers = list(self.object.suppliers.select_related('supplier').all())
        comparison_rows = []
        supplier_totals = []

        for request_item in request_items:
            row_prices = []
            item_prices = []
            for quotation_supplier in quotation_suppliers:
                price = quotation_supplier.item_prices.filter(purchase_request_item=request_item).first()
                row_prices.append(price)
                if price:
                    item_prices.append(price.unit_price)
            best_price = min(item_prices) if item_prices else None
            comparison_rows.append({
                'item': request_item,
                'prices': row_prices,
                'best_price': best_price,
            })

        for quotation_supplier in quotation_suppliers:
            supplier_totals.append((quotation_supplier, quotation_supplier.total_value))

        supplier_totals.sort(key=lambda item: item[1])

        context['request_items'] = request_items
        context['quotation_suppliers'] = quotation_suppliers
        context['comparison_rows'] = comparison_rows
        context['supplier_totals'] = supplier_totals
        context['supplier_form'] = QuotationSupplierForm()
        context['price_form'] = QuotationItemPriceForm()
        context['active_suppliers'] = Supplier.objects.filter(status='active').order_by('legal_name')
        context['missing_prices'] = list(self.object.has_missing_prices())
        context['best_supplier'] = self.object.best_supplier
        return context


class QuotationFinalizeView(LoginRequiredMixin, View):
    def post(self, request, pk):
        quotation = get_object_or_404(Quotation, pk=pk)
        try:
            quotation.finalize()
            messages.success(request, 'Cotação finalizada com sucesso.')
        except Exception as exc:
            messages.error(request, str(exc))
        return redirect('purchases:quotation_detail', pk=quotation.pk)


class QuotationSelectWinnerView(LoginRequiredMixin, View):
    def post(self, request, pk):
        quotation = get_object_or_404(Quotation, pk=pk)
        supplier_id = request.POST.get('winner_supplier')
        invited = quotation.suppliers.filter(pk=supplier_id).select_related('supplier').first()
        if not invited:
            messages.error(request, 'Selecione um fornecedor convidado válido.')
            return redirect('purchases:quotation_detail', pk=quotation.pk)
        quotation.select_winner(invited.supplier)
        messages.success(request, 'Fornecedor vencedor selecionado.')
        return redirect('purchases:quotation_detail', pk=quotation.pk)


class QuotationSupplierCreateView(LoginRequiredMixin, View):
    def post(self, request, quotation_id):
        quotation = get_object_or_404(Quotation, pk=quotation_id)
        form = QuotationSupplierForm(request.POST)
        form.fields['supplier'].queryset = Supplier.objects.filter(status='active')
        if form.is_valid():
            invite = form.save(commit=False)
            invite.quotation = quotation
            invite.save()
            messages.success(request, 'Fornecedor convidado para a cotação.')
        else:
            messages.error(request, 'Não foi possível convidar o fornecedor.')
        return redirect('purchases:quotation_detail', pk=quotation.pk)


class QuotationItemPriceCreateView(LoginRequiredMixin, View):
    def post(self, request, quotation_id):
        quotation = get_object_or_404(Quotation, pk=quotation_id)
        form = QuotationItemPriceForm(request.POST)
        form.fields['quotation_supplier'].queryset = quotation.suppliers.select_related('supplier')
        form.fields['purchase_request_item'].queryset = quotation.purchase_request.items.all()
        if form.is_valid():
            price = form.save(commit=False)
            price.save()
            messages.success(request, 'Preço registrado com sucesso.')
        else:
            messages.error(request, 'Não foi possível registrar o preço.')
        return redirect('purchases:quotation_detail', pk=quotation.pk)


class QuotationItemPriceBySupplierCreateView(LoginRequiredMixin, View):
    def post(self, request, quotation_id, pk):
        quotation = get_object_or_404(Quotation, pk=quotation_id)
        quotation_supplier = get_object_or_404(QuotationSupplier, pk=pk, quotation=quotation)
        form = QuotationItemPriceForm(request.POST)
        form.fields['quotation_supplier'].queryset = quotation.suppliers.select_related('supplier')
        form.fields['purchase_request_item'].queryset = quotation.purchase_request.items.all()
        if form.is_valid():
            price = form.save(commit=False)
            price.quotation_supplier = quotation_supplier
            price.save()
            messages.success(request, 'Preço registrado para o fornecedor selecionado.')
        else:
            messages.error(request, 'Não foi possível registrar o preço.')
        return redirect('purchases:quotation_detail', pk=quotation.pk)


class PurchaseOrderGenerateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        quotation = get_object_or_404(Quotation, pk=pk)
        try:
            order = PurchaseOrder.create_from_quotation(quotation)
            messages.success(request, 'Ordem de compra gerada com sucesso.')
            return redirect('purchases:order_detail', pk=order.pk)
        except Exception as exc:
            messages.error(request, str(exc))
            return redirect('purchases:quotation_detail', pk=quotation.pk)


class PurchaseOrderDetailView(LoginRequiredMixin, DetailView):
    model = PurchaseOrder
    template_name = 'purchases/order_detail.html'
    context_object_name = 'order'
    queryset = PurchaseOrder.objects.select_related('purchase_request', 'quotation', 'supplier').prefetch_related('items')


class PurchaseOrderApproveView(LoginRequiredMixin, View):
    def post(self, request, pk):
        order = get_object_or_404(PurchaseOrder, pk=pk)
        order.approve()
        messages.success(request, 'Ordem de compra aprovada com sucesso.')
        return redirect('purchases:order_detail', pk=order.pk)


class QuotationDeleteView(PostDeleteView):
    model = Quotation
    success_url = reverse_lazy('purchases:request_list')
    success_message = 'Cotação excluída com sucesso.'


class PurchaseOrderDeleteView(PostDeleteView):
    model = PurchaseOrder
    success_url = reverse_lazy('purchases:request_list')
    success_message = 'Ordem de compra excluída com sucesso.'
