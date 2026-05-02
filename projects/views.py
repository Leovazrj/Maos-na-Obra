import json
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import DailyLogForm, PhysicalMeasurementForm, ProjectForm, ProjectTaskForm
from .models import DailyLog, PhysicalMeasurement, Project, ProjectTask


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('customer', 'responsible').filter(status='active')
        search = self.request.GET.get('search')
        status = self.request.GET.get('status')

        if status:
            queryset = super().get_queryset().select_related('customer', 'responsible').filter(status=status)
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(customer__name__icontains=search))

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['selected_status'] = self.request.GET.get('status', '')
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:list')

    def form_valid(self, form):
        messages.success(self.request, 'Obra cadastrada com sucesso!')
        return super().form_valid(form)


class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'

    def get_success_url(self):
        return reverse('projects:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Obra atualizada com sucesso!')
        return super().form_valid(form)


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'
    queryset = Project.objects.select_related('customer', 'responsible').prefetch_related('tasks', 'measurements', 'daily_logs')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        log_date = self.request.GET.get('log_date')
        daily_logs = self.object.daily_logs.all()
        if log_date:
            daily_logs = daily_logs.filter(log_date=log_date)

        context['daily_logs'] = daily_logs
        context['log_date'] = log_date or ''
        context['daily_log_form'] = DailyLogForm()
        context['task_form'] = ProjectTaskForm()
        context['measurement_form'] = PhysicalMeasurementForm(project=self.object)
        context['measurements'] = self.object.measurements.select_related('task')
        context['gantt_data'] = json.dumps(self._build_gantt_data())
        return context

    def _build_gantt_data(self):
        data = []
        for task in self.object.tasks.all():
            latest_measurement = task.measurements.order_by('-measurement_date', '-created_at').first()
            progress = latest_measurement.measured_percentage if latest_measurement else Decimal('0.00')
            data.append({
                'id': task.pk,
                'name': task.name,
                'start': task.planned_start_date.isoformat(),
                'end': task.planned_end_date.isoformat(),
                'plannedPercentage': float(task.planned_percentage),
                'progress': float(progress),
            })
        return data


class ProjectCloseView(LoginRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        project.status = 'closed'
        project.save(update_fields=['status', 'updated_at'])
        messages.success(request, 'Obra encerrada com sucesso.')
        return redirect('projects:detail', pk=project.pk)


class ProjectChildCreateMixin(LoginRequiredMixin, CreateView):
    project = None

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.project = self.project
        messages.success(self.request, self.success_message)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('projects:detail', kwargs={'pk': self.project.pk})


class ProjectChildUpdateMixin(LoginRequiredMixin, UpdateView):
    project = None

    def dispatch(self, request, *args, **kwargs):
        self.project = get_object_or_404(Project, pk=self.kwargs['project_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(project=self.project)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['project'] = self.project
        return context

    def form_valid(self, form):
        messages.success(self.request, self.success_message)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('projects:detail', kwargs={'pk': self.project.pk})


class DailyLogCreateView(ProjectChildCreateMixin):
    model = DailyLog
    form_class = DailyLogForm
    success_message = 'Diário de obra registrado com sucesso.'


class DailyLogUpdateView(ProjectChildUpdateMixin):
    model = DailyLog
    form_class = DailyLogForm
    template_name = 'projects/daily_log_form.html'
    success_message = 'Diário de obra atualizado com sucesso.'


class ProjectTaskCreateView(ProjectChildCreateMixin):
    model = ProjectTask
    form_class = ProjectTaskForm
    success_message = 'Tarefa da obra cadastrada com sucesso.'


class ProjectTaskUpdateView(ProjectChildUpdateMixin):
    model = ProjectTask
    form_class = ProjectTaskForm
    template_name = 'projects/project_task_form.html'
    success_message = 'Tarefa da obra atualizada com sucesso.'


class PhysicalMeasurementCreateView(ProjectChildCreateMixin):
    model = PhysicalMeasurement
    form_class = PhysicalMeasurementForm
    success_message = 'Medição física registrada com sucesso.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.project
        return kwargs


class PhysicalMeasurementUpdateView(ProjectChildUpdateMixin):
    model = PhysicalMeasurement
    form_class = PhysicalMeasurementForm
    template_name = 'projects/physical_measurement_form.html'
    success_message = 'Medição física atualizada com sucesso.'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.project
        return kwargs
