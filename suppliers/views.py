from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.views import PostDeleteView
from .forms import SupplierForm
from .models import Supplier, SupplierCategory


class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'suppliers/supplier_list.html'
    context_object_name = 'suppliers'

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .prefetch_related('categories')
        )
        search = self.request.GET.get('search')
        category = self.request.GET.get('category')
        status = self.request.GET.get('status')

        if search:
            queryset = queryset.filter(
                Q(legal_name__icontains=search)
                | Q(trade_name__icontains=search)
                | Q(document_number__icontains=search)
                | Q(email__icontains=search)
            )
        if category:
            queryset = queryset.filter(categories__pk=category)
        if status:
            queryset = queryset.filter(status=status)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = SupplierCategory.objects.all()
        context['selected_category'] = self.request.GET.get('category', '')
        context['selected_status'] = self.request.GET.get('status', '')
        context['search'] = self.request.GET.get('search', '')
        return context


class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'suppliers/supplier_form.html'
    success_url = reverse_lazy('suppliers:list')

    def form_valid(self, form):
        messages.success(self.request, 'Fornecedor cadastrado com sucesso!')
        return super().form_valid(form)


class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    form_class = SupplierForm
    template_name = 'suppliers/supplier_form.html'

    def get_success_url(self):
        return reverse('suppliers:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Fornecedor atualizado com sucesso!')
        return super().form_valid(form)


class SupplierDeleteView(PostDeleteView):
    model = Supplier
    success_url = reverse_lazy('suppliers:list')
    success_message = 'Fornecedor excluído com sucesso.'

    def delete_object(self, obj):
        obj.accounts_payable.all().delete()
        obj.purchase_orders.all().delete()
        return super().delete_object(obj)


class SupplierDetailView(LoginRequiredMixin, DetailView):
    model = Supplier
    template_name = 'suppliers/supplier_detail.html'
    context_object_name = 'supplier'
    queryset = Supplier.objects.prefetch_related(
        Prefetch('categories', queryset=SupplierCategory.objects.order_by('name'))
    )


class SupplierInactivateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk)
        supplier.status = 'inactive'
        supplier.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'Fornecedor inativado com sucesso.')
        return redirect('suppliers:detail', pk=supplier.pk)
