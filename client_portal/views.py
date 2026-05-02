from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, TemplateView

from customers.models import Customer
from projects.models import Project

from .models import ClientPortalAccess


class ClientPortalAccessMixin(LoginRequiredMixin):
    portal_customer = None
    portal_access = None

    def get_authorized_accesses(self):
        return ClientPortalAccess.objects.filter(
            user=self.request.user,
            is_active=True,
        ).select_related('customer')

    def get_authorized_customer(self, customer_id=None):
        queryset = self.get_authorized_accesses()
        if customer_id is None:
            return None
        access = queryset.filter(customer_id=customer_id).first()
        if not access:
            raise PermissionDenied('Você não possui acesso ao portal deste cliente.')
        self.portal_access = access
        self.portal_customer = access.customer
        return access.customer

    def ensure_has_access(self):
        if not self.get_authorized_accesses().exists():
            raise PermissionDenied('Você não possui acesso ao portal do cliente.')


class ClientPortalHomeView(ClientPortalAccessMixin, TemplateView):
    template_name = 'client_portal/home.html'

    def get_context_data(self, **kwargs):
        self.ensure_has_access()
        context = super().get_context_data(**kwargs)
        accesses = self.get_authorized_accesses().select_related('customer')
        context['accesses'] = accesses
        context['customers'] = [access.customer for access in accesses]
        return context


class CustomerPortalDetailView(ClientPortalAccessMixin, DetailView):
    model = Customer
    template_name = 'client_portal/customer_detail.html'
    context_object_name = 'customer'
    pk_url_kwarg = 'customer_id'

    def get_object(self, queryset=None):
        customer = super().get_object(queryset)
        self.get_authorized_customer(customer.pk)
        return customer

    def get_queryset(self):
        return Customer.objects.prefetch_related('projects')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = self.object.projects.select_related('responsible').prefetch_related('tasks', 'measurements')
        context['documents'] = self.object.documents.filter(visible_in_portal=True)
        context['photos'] = self.object.photos.filter(visible_in_portal=True)
        return context


class ProjectPortalDetailView(ClientPortalAccessMixin, DetailView):
    model = Project
    template_name = 'client_portal/project_detail.html'
    context_object_name = 'project'
    pk_url_kwarg = 'pk'

    def get_object(self, queryset=None):
        customer = self.get_authorized_customer(self.kwargs['customer_id'])
        return get_object_or_404(
            Project.objects.select_related('customer', 'responsible').prefetch_related('tasks', 'measurements'),
            pk=self.kwargs['pk'],
            customer=customer,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customer'] = self.object.customer
        context['documents'] = self.object.customer.documents.filter(visible_in_portal=True)
        context['photos'] = self.object.customer.photos.filter(visible_in_portal=True)
        context['measurements'] = self.object.measurements.filter(visible_in_portal=True).select_related('task')
        context['empty_state'] = not context['documents'].exists() and not context['photos'].exists() and not context['measurements'].exists()
        return context
