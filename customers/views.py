from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from .models import Customer, CustomerInteraction, CustomerDocument, CustomerPhoto
from .forms import CustomerForm, CustomerInteractionForm, CustomerDocumentForm, CustomerPhotoForm


class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(name__icontains=search)
        return queryset


class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customers:list')

    def form_valid(self, form):
        messages.success(self.request, 'Cliente cadastrado com sucesso!')
        return super().form_valid(form)


class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'

    def get_success_url(self):
        return reverse('customers:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Cliente atualizado com sucesso!')
        return super().form_valid(form)


class CustomerDetailView(LoginRequiredMixin, DetailView):
    model = Customer
    template_name = 'customers/customer_detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['interaction_form'] = CustomerInteractionForm()
        context['document_form'] = CustomerDocumentForm()
        context['photo_form'] = CustomerPhotoForm()
        return context


class CustomerInteractionCreateView(LoginRequiredMixin, CreateView):
    model = CustomerInteraction
    form_class = CustomerInteractionForm

    def form_valid(self, form):
        customer = get_object_or_404(Customer, pk=self.kwargs['customer_id'])
        form.instance.customer = customer
        form.instance.user = self.request.user
        messages.success(self.request, 'Interação registrada com sucesso.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao registrar interação. Verifique os dados.')
        return redirect('customers:detail', pk=self.kwargs['customer_id'])

    def get_success_url(self):
        return reverse('customers:detail', kwargs={'pk': self.kwargs['customer_id']})


class CustomerDocumentCreateView(LoginRequiredMixin, CreateView):
    model = CustomerDocument
    form_class = CustomerDocumentForm

    def form_valid(self, form):
        customer = get_object_or_404(Customer, pk=self.kwargs['customer_id'])
        form.instance.customer = customer
        messages.success(self.request, 'Documento anexado com sucesso.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao anexar documento.')
        return redirect('customers:detail', pk=self.kwargs['customer_id'])

    def get_success_url(self):
        return reverse('customers:detail', kwargs={'pk': self.kwargs['customer_id']})


class CustomerPhotoCreateView(LoginRequiredMixin, CreateView):
    model = CustomerPhoto
    form_class = CustomerPhotoForm

    def form_valid(self, form):
        customer = get_object_or_404(Customer, pk=self.kwargs['customer_id'])
        form.instance.customer = customer
        messages.success(self.request, 'Foto anexada com sucesso.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Erro ao anexar foto.')
        return redirect('customers:detail', pk=self.kwargs['customer_id'])

    def get_success_url(self):
        return reverse('customers:detail', kwargs={'pk': self.kwargs['customer_id']})
