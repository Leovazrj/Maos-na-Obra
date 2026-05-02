from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from core.models import TimeStampedModel


class InputItem(TimeStampedModel):
    name = models.CharField('Nome', max_length=255)
    unit = models.CharField('Unidade', max_length=20)
    unit_cost = models.DecimalField(
        'Custo unitário',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00'),
    )
    description = models.TextField('Descrição', blank=True, null=True)
    is_active = models.BooleanField('Ativo', default=True)

    class Meta:
        verbose_name = 'Insumo'
        verbose_name_plural = 'Insumos'
        ordering = ['name']

    def __str__(self):
        return self.name


class Budget(TimeStampedModel):
    BUDGET_TYPE_CHOICES = [
        ('cost', 'Custo'),
        ('sale', 'Venda'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('approved', 'Aprovado'),
        ('archived', 'Arquivado'),
    ]

    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='budgets')
    name = models.CharField('Nome', max_length=255)
    budget_type = models.CharField('Tipo', max_length=20, choices=BUDGET_TYPE_CHOICES, default='cost')
    margin_percentage = models.DecimalField(
        'Margem ou taxa (%)',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('0.00'),
    )
    cost_total = models.DecimalField('Total de custo', max_digits=12, decimal_places=2, default=Decimal('0.00'))
    sale_total = models.DecimalField('Total de venda', max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField('Observações', blank=True, null=True)

    class Meta:
        verbose_name = 'Orçamento'
        verbose_name_plural = 'Orçamentos'
        ordering = ['-created_at', 'name']

    def __str__(self):
        return self.name

    def recalculate_totals(self, commit=True):
        cost_total = sum((item.cost_total for item in self.items.all()), Decimal('0.00'))
        self.cost_total = cost_total.quantize(Decimal('0.01'))
        self.sale_total = (self.cost_total * (Decimal('1.00') + self.margin_percentage / Decimal('100.00'))).quantize(Decimal('0.01'))
        if commit:
            self.save(update_fields=['cost_total', 'sale_total', 'updated_at'])
        return self.cost_total, self.sale_total


class BudgetItem(TimeStampedModel):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='items')
    name = models.CharField('Serviço', max_length=255)
    unit = models.CharField('Unidade', max_length=20)
    quantity = models.DecimalField(
        'Quantidade',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('1.00'),
    )
    cost_total = models.DecimalField('Custo total', max_digits=12, decimal_places=2, default=Decimal('0.00'))
    sale_total = models.DecimalField('Venda total', max_digits=12, decimal_places=2, default=Decimal('0.00'))
    description = models.TextField('Descrição', blank=True, null=True)

    class Meta:
        verbose_name = 'Item do Orçamento'
        verbose_name_plural = 'Itens do Orçamento'
        ordering = ['created_at', 'name']

    def __str__(self):
        return self.name

    def recalculate_totals(self, commit=True):
        self.cost_total = sum((composition.cost_total for composition in self.composition_items.all()), Decimal('0.00')).quantize(Decimal('0.01'))
        self.sale_total = (self.cost_total * (Decimal('1.00') + self.budget.margin_percentage / Decimal('100.00'))).quantize(Decimal('0.01'))
        if commit:
            self.save(update_fields=['cost_total', 'sale_total', 'updated_at'])
            self.budget.recalculate_totals()
        return self.cost_total, self.sale_total


class BudgetCompositionItem(TimeStampedModel):
    budget_item = models.ForeignKey(BudgetItem, on_delete=models.CASCADE, related_name='composition_items')
    input_item = models.ForeignKey(InputItem, on_delete=models.PROTECT, related_name='budget_compositions')
    unit = models.CharField('Unidade', max_length=20)
    quantity = models.DecimalField(
        'Quantidade',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    unit_cost = models.DecimalField(
        'Custo unitário',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    cost_total = models.DecimalField('Custo total', max_digits=12, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = 'Item de Composição'
        verbose_name_plural = 'Itens de Composição'
        ordering = ['created_at']

    def __str__(self):
        return f'{self.input_item.name} em {self.budget_item.name}'

    def save(self, *args, **kwargs):
        self.cost_total = (self.quantity * self.unit_cost).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)
        self.budget_item.recalculate_totals()

    def delete(self, *args, **kwargs):
        budget_item = self.budget_item
        result = super().delete(*args, **kwargs)
        budget_item.recalculate_totals()
        return result
