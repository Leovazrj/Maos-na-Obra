from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from core.views import PostDeleteView
from .forms import BudgetCompositionItemForm, BudgetForm, BudgetItemForm, InputItemForm
from .models import Budget, BudgetCompositionItem, BudgetItem, InputItem


class InputItemListView(LoginRequiredMixin, ListView):
    model = InputItem
    template_name = 'budgets/input_item_list.html'
    context_object_name = 'input_items'

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(description__icontains=search))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        return context


class InputItemCreateView(LoginRequiredMixin, CreateView):
    model = InputItem
    form_class = InputItemForm
    template_name = 'budgets/input_item_form.html'
    success_url = reverse_lazy('budgets:input_item_list')

    def form_valid(self, form):
        messages.success(self.request, 'Insumo cadastrado com sucesso!')
        return super().form_valid(form)


class InputItemUpdateView(LoginRequiredMixin, UpdateView):
    model = InputItem
    form_class = InputItemForm
    template_name = 'budgets/input_item_form.html'
    success_url = reverse_lazy('budgets:input_item_list')

    def form_valid(self, form):
        messages.success(self.request, 'Insumo atualizado com sucesso!')
        return super().form_valid(form)


class InputItemDeleteView(PostDeleteView):
    model = InputItem
    success_url = reverse_lazy('budgets:input_item_list')
    success_message = 'Insumo excluído com sucesso.'

    def delete_object(self, obj):
        obj.budget_compositions.all().delete()
        return super().delete_object(obj)


class BudgetListView(LoginRequiredMixin, ListView):
    model = Budget
    template_name = 'budgets/budget_list.html'
    context_object_name = 'budgets'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('project')
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(project__name__icontains=search))
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        return context


class BudgetCreateView(LoginRequiredMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'budgets/budget_form.html'
    success_url = reverse_lazy('budgets:list')

    def form_valid(self, form):
        messages.success(self.request, 'Orçamento cadastrado com sucesso!')
        return super().form_valid(form)


class BudgetUpdateView(LoginRequiredMixin, UpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'budgets/budget_form.html'

    def get_success_url(self):
        return reverse('budgets:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.recalculate_totals()
        messages.success(self.request, 'Orçamento atualizado com sucesso!')
        return response


class BudgetDeleteView(PostDeleteView):
    model = Budget
    success_url = reverse_lazy('budgets:list')
    success_message = 'Orçamento excluído com sucesso.'


class BudgetDetailView(LoginRequiredMixin, DetailView):
    model = Budget
    template_name = 'budgets/budget_detail.html'
    context_object_name = 'budget'
    queryset = Budget.objects.select_related('project').prefetch_related('items__composition_items__input_item')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['budget_item_form'] = BudgetItemForm()
        context['composition_form'] = BudgetCompositionItemForm()
        return context


class BudgetChildCreateMixin(LoginRequiredMixin, CreateView):
    budget = None

    def dispatch(self, request, *args, **kwargs):
        self.budget = get_object_or_404(Budget, pk=self.kwargs['budget_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('budgets:detail', kwargs={'pk': self.budget.pk})


class BudgetChildUpdateMixin(LoginRequiredMixin, UpdateView):
    budget = None

    def dispatch(self, request, *args, **kwargs):
        self.budget = get_object_or_404(Budget, pk=self.kwargs['budget_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['budget'] = self.budget
        return context

    def get_success_url(self):
        return reverse('budgets:detail', kwargs={'pk': self.budget.pk})


class BudgetItemCreateView(BudgetChildCreateMixin):
    model = BudgetItem
    form_class = BudgetItemForm

    def form_valid(self, form):
        form.instance.budget = self.budget
        messages.success(self.request, 'Item adicionado ao orçamento.')
        response = super().form_valid(form)
        self.object.recalculate_totals()
        return response


class BudgetItemUpdateView(BudgetChildUpdateMixin):
    model = BudgetItem
    form_class = BudgetItemForm
    template_name = 'budgets/budget_item_form.html'

    def get_queryset(self):
        return super().get_queryset().filter(budget=self.budget)

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.recalculate_totals()
        messages.success(self.request, 'Item do orçamento atualizado.')
        return response


class BudgetItemDeleteView(LoginRequiredMixin, View):
    def post(self, request, budget_id, pk):
        budget = get_object_or_404(Budget, pk=budget_id)
        budget_item = get_object_or_404(BudgetItem, pk=pk, budget=budget)
        budget_item.composition_items.all().delete()
        budget_item.delete()
        budget.recalculate_totals()
        messages.success(request, 'Item do orçamento excluído com sucesso.')
        return redirect('budgets:detail', pk=budget.pk)


class BudgetCompositionItemCreateView(BudgetChildCreateMixin):
    model = BudgetCompositionItem
    form_class = BudgetCompositionItemForm

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        return response

    def form_valid(self, form):
        budget_item = get_object_or_404(BudgetItem, pk=self.kwargs['item_id'], budget=self.budget)
        form.instance.budget_item = budget_item
        messages.success(self.request, 'Insumo adicionado à composição.')
        return super().form_valid(form)


class BudgetCompositionItemDeleteView(LoginRequiredMixin, View):
    def post(self, request, budget_id, item_id, pk):
        budget = get_object_or_404(Budget, pk=budget_id)
        budget_item = get_object_or_404(BudgetItem, pk=item_id, budget=budget)
        composition = get_object_or_404(BudgetCompositionItem, pk=pk, budget_item=budget_item)
        composition.delete()
        messages.success(request, 'Insumo removido da composição.')
        return redirect('budgets:detail', pk=budget.pk)
