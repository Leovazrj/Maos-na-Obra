from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from core.views import PostDeleteView
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


class CustomerDeleteView(PostDeleteView):
    model = Customer
    success_url = reverse_lazy('customers:list')
    success_message = 'Cliente excluído com sucesso.'

    def delete_object(self, obj):
        obj.projects.all().delete()
        obj.portal_accesses.all().delete()
        return super().delete_object(obj)


class CustomerRelatedDeleteMixin(LoginRequiredMixin, View):
    model = None
    success_message = 'Registro excluído com sucesso.'

    def dispatch(self, request, *args, **kwargs):
        self.customer = get_object_or_404(Customer, pk=self.kwargs['customer_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_object(self):
        if self.model is None:
            raise AttributeError('Defina model na view de exclusão.')
        return get_object_or_404(self.model, pk=self.kwargs['pk'], customer=self.customer)

    def delete_related(self, obj):
        return None

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        self.delete_related(obj)
        obj.delete()
        messages.success(request, self.success_message)
        return redirect('customers:detail', pk=self.customer.pk)


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


class CustomerInteractionDeleteView(CustomerRelatedDeleteMixin):
    model = CustomerInteraction
    success_message = 'Interação excluída com sucesso.'


class CustomerDocumentDeleteView(CustomerRelatedDeleteMixin):
    model = CustomerDocument
    success_message = 'Documento excluído com sucesso.'

    def delete_related(self, obj):
        if obj.file:
            obj.file.delete(save=False)


class CustomerPhotoDeleteView(CustomerRelatedDeleteMixin):
    model = CustomerPhoto
    success_message = 'Foto excluída com sucesso.'

    def delete_related(self, obj):
        if obj.image:
            obj.image.delete(save=False)
