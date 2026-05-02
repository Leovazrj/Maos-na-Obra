from django.urls import reverse_lazy, reverse
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView

from core.views import PostDeleteView
from core.pdf_reports import (
    body,
    build_data_table,
    build_key_value_table,
    build_pdf_response,
    format_value,
    heading,
    spacer,
    subheading,
)
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
        context['customer_interactions'] = self.object.interactions.select_related('user')
        context['customer_documents'] = self.object.documents.all()
        context['customer_photos'] = self.object.photos.all()
        context['projects_count'] = self.object.projects.count()
        context['interactions_count'] = self.object.interactions.count()
        context['documents_count'] = self.object.documents.count()
        context['photos_count'] = self.object.photos.count()
        return context


class CustomerReportPdfView(LoginRequiredMixin, View):
    def get(self, request, pk):
        customer = get_object_or_404(
            Customer.objects.prefetch_related('projects', 'interactions', 'documents', 'photos'),
            pk=pk,
        )
        rows = [
            ('Tipo', customer.get_person_type_display()),
            ('Documento', customer.document_number or '-'),
            ('Email', customer.email or '-'),
            ('Telefone', customer.phone or '-'),
            ('Endereço', customer.address or '-'),
        ]
        project_rows = [
            [
                project.name,
                project.get_status_display(),
                format_value(project.expected_start_date),
                format_value(project.expected_end_date),
            ]
            for project in customer.projects.all().order_by('-created_at')[:10]
        ]
        interaction_rows = [
            [
                format_value(interaction.interaction_date),
                interaction.get_interaction_type_display(),
                interaction.description[:80],
            ]
            for interaction in customer.interactions.all().order_by('-interaction_date', '-created_at')[:10]
        ]
        doc_rows = [[doc.title, 'Portal' if doc.visible_in_portal else 'Interno'] for doc in customer.documents.all().order_by('-created_at')[:10]]
        photo_rows = [[photo.title, format_value(photo.created_at)] for photo in customer.photos.all().order_by('-created_at')[:10]]

        story = [
            heading(f'Relatório do cliente: {customer.name}'),
            body('Resumo de contato, obras e registros associados ao cliente.'),
            spacer(8),
            build_key_value_table(rows),
            spacer(8),
            subheading('Obras'),
            build_data_table(['Obra', 'Status', 'Início', 'Término'], project_rows or [['-', '-', '-', '-']]),
            spacer(8),
            subheading('Interações recentes'),
            build_data_table(['Data', 'Tipo', 'Descrição'], interaction_rows or [['-', '-', '-']]),
            spacer(8),
            subheading('Documentos e fotos'),
            build_data_table(['Documento', 'Visibilidade'], doc_rows or [['-', '-']]),
            spacer(4),
            build_data_table(['Foto', 'Data'], photo_rows or [['-', '-']]),
        ]
        return build_pdf_response(f'cliente-{customer.pk}.pdf', f'Relatório do cliente {customer.name}', story)


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
