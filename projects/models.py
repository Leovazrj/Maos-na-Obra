from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from core.models import TimeStampedModel


class Project(TimeStampedModel):
    STATUS_CHOICES = [
        ('active', 'Ativa'),
        ('paused', 'Pausada'),
        ('closed', 'Encerrada'),
        ('inactive', 'Inativa'),
    ]

    name = models.CharField('Nome', max_length=255)
    customer = models.ForeignKey('customers.Customer', on_delete=models.PROTECT, related_name='projects')
    address = models.TextField('Endereço', blank=True, null=True)
    expected_start_date = models.DateField('Data prevista de início', blank=True, null=True)
    expected_end_date = models.DateField('Data prevista de término', blank=True, null=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='active')
    expected_value = models.DecimalField('Valor previsto', max_digits=12, decimal_places=2, default=Decimal('0.00'))
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='responsible_projects',
    )
    description = models.TextField('Descrição', blank=True, null=True)

    class Meta:
        verbose_name = 'Obra'
        verbose_name_plural = 'Obras'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def physical_progress_percent(self):
        weighted_progress = Decimal('0.00')
        planned_total = Decimal('0.00')

        for task in self.tasks.all():
            planned_percentage = task.planned_percentage or Decimal('0.00')
            planned_total += planned_percentage
            latest_measurement = task.measurements.order_by('-measurement_date', '-created_at').first()
            if latest_measurement:
                weighted_progress += latest_measurement.measured_percentage * planned_percentage / Decimal('100.00')

        if not planned_total:
            return Decimal('0.00')

        return weighted_progress.quantize(Decimal('0.01'))


class DailyLog(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='daily_logs')
    log_date = models.DateField('Data')
    weather = models.CharField('Clima', max_length=120, blank=True, null=True)
    team_present = models.TextField('Equipe presente', blank=True, null=True)
    services_performed = models.TextField('Serviços executados')
    occurrences = models.TextField('Ocorrências', blank=True, null=True)
    notes = models.TextField('Observações', blank=True, null=True)

    class Meta:
        verbose_name = 'Diário de Obra'
        verbose_name_plural = 'Diários de Obra'
        ordering = ['-log_date', '-created_at']

    def __str__(self):
        return f'{self.project.name} - {self.log_date:%d/%m/%Y}'


class ProjectTask(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    name = models.CharField('Serviço ou etapa', max_length=255)
    planned_start_date = models.DateField('Início planejado')
    planned_end_date = models.DateField('Término planejado')
    planned_percentage = models.DecimalField(
        'Percentual planejado',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
    )
    planned_cost = models.DecimalField('Custo planejado', max_digits=12, decimal_places=2, default=Decimal('0.00'))
    description = models.TextField('Descrição', blank=True, null=True)

    class Meta:
        verbose_name = 'Tarefa da Obra'
        verbose_name_plural = 'Tarefas da Obra'
        ordering = ['planned_start_date', 'planned_end_date', 'name']

    def __str__(self):
        return f'{self.project.name} - {self.name}'


class PhysicalMeasurement(TimeStampedModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='measurements')
    task = models.ForeignKey(ProjectTask, on_delete=models.CASCADE, related_name='measurements')
    measurement_date = models.DateField('Data da medição')
    measured_percentage = models.DecimalField(
        'Percentual medido',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
    )
    measured_value = models.DecimalField('Valor medido', max_digits=12, decimal_places=2, default=Decimal('0.00'))
    visible_in_portal = models.BooleanField('Visível no Portal do Cliente', default=False)
    notes = models.TextField('Observações', blank=True, null=True)

    class Meta:
        verbose_name = 'Medição Física'
        verbose_name_plural = 'Medições Físicas'
        ordering = ['-measurement_date', '-created_at']

    def __str__(self):
        return f'{self.task.name} - {self.measured_percentage}%'
