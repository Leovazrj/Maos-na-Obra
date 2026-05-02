from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from core.models import TimeStampedModel


class PurchaseRequest(TimeStampedModel):
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('open', 'Aberta'),
        ('quoted', 'Cotada'),
        ('ordered', 'Ordenada'),
        ('cancelled', 'Cancelada'),
    ]

    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='purchase_requests')
    title = models.CharField('Título', max_length=255)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField('Observações', blank=True, null=True)

    class Meta:
        verbose_name = 'Solicitação de Compra'
        verbose_name_plural = 'Solicitações de Compra'
        ordering = ['-created_at', 'title']

    def __str__(self):
        return self.title

    @property
    def total_items(self):
        return self.items.count()

    def open_quotation(self):
        self.status = 'open'
        self.save(update_fields=['status', 'updated_at'])


class PurchaseRequestItem(TimeStampedModel):
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='items')
    input_item = models.ForeignKey('budgets.InputItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_request_items')
    description = models.CharField('Descrição', max_length=255)
    unit = models.CharField('Unidade', max_length=20)
    quantity = models.DecimalField(
        'Quantidade',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        default=Decimal('1.00'),
    )
    notes = models.TextField('Observações', blank=True, null=True)

    class Meta:
        verbose_name = 'Item Solicitado'
        verbose_name_plural = 'Itens Solicitados'
        ordering = ['created_at', 'description']

    def __str__(self):
        return self.description


class Quotation(TimeStampedModel):
    STATUS_CHOICES = [
        ('open', 'Aberta'),
        ('responded', 'Respondida'),
        ('finished', 'Finalizada'),
    ]

    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='quotations')
    title = models.CharField('Título', max_length=255)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='open')
    winner_supplier = models.ForeignKey(
        'suppliers.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_quotations',
    )
    notes = models.TextField('Observações', blank=True, null=True)

    class Meta:
        verbose_name = 'Cotação'
        verbose_name_plural = 'Cotações'
        ordering = ['-created_at', 'title']

    def __str__(self):
        return self.title

    @property
    def total_suppliers(self):
        return self.suppliers.count()

    @property
    def supplier_totals(self):
        totals = []
        for quotation_supplier in self.suppliers.select_related('supplier').all():
            total = quotation_supplier.total_value
            if quotation_supplier.has_all_item_prices:
                totals.append((quotation_supplier, total))
        totals.sort(key=lambda item: item[1])
        return totals

    @property
    def best_supplier(self):
        if self.winner_supplier:
            return self.suppliers.filter(supplier=self.winner_supplier).first()
        totals = self.supplier_totals
        return totals[0][0] if totals else None

    @property
    def total_value(self):
        best_supplier = self.best_supplier
        if best_supplier:
            return best_supplier.total_value
        return Decimal('0.00')

    def has_missing_prices(self):
        requested_ids = set(self.purchase_request.items.values_list('id', flat=True))
        priced_ids = set(
            QuotationItemPrice.objects.filter(
                quotation_supplier__quotation=self,
            ).values_list('purchase_request_item_id', flat=True).distinct()
        )
        return requested_ids - priced_ids

    def finalize(self):
        missing = self.has_missing_prices()
        if missing:
            raise ValidationError('Existem itens da solicitação sem preço informado.')

        best_supplier = self.best_supplier
        if not best_supplier:
            raise ValidationError('Não foi possível identificar um fornecedor vencedor.')

        self.winner_supplier = best_supplier.supplier
        self.status = 'finished'
        self.save(update_fields=['winner_supplier', 'status', 'updated_at'])
        return self

    def select_winner(self, supplier):
        self.winner_supplier = supplier
        if self.status == 'open':
            self.status = 'responded'
        self.save(update_fields=['winner_supplier', 'status', 'updated_at'])
        return self


class QuotationSupplier(TimeStampedModel):
    STATUS_CHOICES = [
        ('invited', 'Convidado'),
        ('responded', 'Respondido'),
        ('declined', 'Recusado'),
    ]

    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='suppliers')
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.CASCADE, related_name='quotation_invites')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='invited')
    invited_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField('Observações', blank=True, null=True)

    class Meta:
        verbose_name = 'Fornecedor Convidado'
        verbose_name_plural = 'Fornecedores Convidados'
        ordering = ['supplier__legal_name']
        constraints = [
            models.UniqueConstraint(fields=['quotation', 'supplier'], name='unique_quotation_supplier'),
        ]

    def __str__(self):
        return self.supplier.legal_name

    @property
    def has_all_item_prices(self):
        return self.quotation.purchase_request.items.count() > 0 and self.item_prices.values('purchase_request_item').distinct().count() == self.quotation.purchase_request.items.count()

    @property
    def total_value(self):
        return sum((price.total_price for price in self.item_prices.all()), Decimal('0.00')).quantize(Decimal('0.01'))


class QuotationItemPrice(TimeStampedModel):
    quotation_supplier = models.ForeignKey(QuotationSupplier, on_delete=models.CASCADE, related_name='item_prices')
    purchase_request_item = models.ForeignKey(PurchaseRequestItem, on_delete=models.CASCADE, related_name='quotation_prices')
    unit_price = models.DecimalField(
        'Preço unitário',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    notes = models.TextField('Observações', blank=True, null=True)

    class Meta:
        verbose_name = 'Preço por Item'
        verbose_name_plural = 'Preços por Item'
        ordering = ['created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['quotation_supplier', 'purchase_request_item'],
                name='unique_quotation_item_price',
            ),
        ]

    def __str__(self):
        return f'{self.purchase_request_item.description} - {self.quotation_supplier.supplier.legal_name}'

    @property
    def total_price(self):
        return (self.unit_price * self.purchase_request_item.quantity).quantize(Decimal('0.01'))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.quotation_supplier.status = 'responded'
        self.quotation_supplier.save(update_fields=['status', 'updated_at'])
        if self.quotation_supplier.quotation.status == 'open':
            self.quotation_supplier.quotation.status = 'responded'
            self.quotation_supplier.quotation.save(update_fields=['status', 'updated_at'])


class PurchaseOrder(TimeStampedModel):
    STATUS_CHOICES = [
        ('draft', 'Rascunho'),
        ('approved', 'Aprovada'),
        ('cancelled', 'Cancelada'),
    ]

    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE, related_name='purchase_orders')
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='purchase_orders')
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.PROTECT, related_name='purchase_orders')
    title = models.CharField('Título', max_length=255)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField('Observações', blank=True, null=True)

    class Meta:
        verbose_name = 'Ordem de Compra'
        verbose_name_plural = 'Ordens de Compra'
        ordering = ['-created_at', 'title']

    def __str__(self):
        return self.title

    @property
    def total_value(self):
        return sum((item.total_price for item in self.items.all()), Decimal('0.00')).quantize(Decimal('0.01'))

    def approve(self):
        from finance.services import create_payable_from_purchase_order

        self.status = 'approved'
        self.save(update_fields=['status', 'updated_at'])
        create_payable_from_purchase_order(self)

    @classmethod
    def create_from_quotation(cls, quotation):
        quotation.finalize()
        winner = quotation.best_supplier
        if not winner:
            raise ValidationError('Nenhum fornecedor vencedor disponível.')

        order = cls.objects.create(
            purchase_request=quotation.purchase_request,
            quotation=quotation,
            supplier=winner.supplier,
            title=f'OC - {quotation.title}',
        )
        request_items = list(quotation.purchase_request.items.all())
        for request_item in request_items:
            price = winner.item_prices.filter(purchase_request_item=request_item).first()
            if not price:
                raise ValidationError('Fornecedor vencedor não possui preço para todos os itens.')
            PurchaseOrderItem.objects.create(
                purchase_order=order,
                purchase_request_item=request_item,
                description=request_item.description,
                unit=request_item.unit,
                quantity=request_item.quantity,
                unit_price=price.unit_price,
            )
        order.save(update_fields=['updated_at'])
        quotation.purchase_request.status = 'ordered'
        quotation.purchase_request.save(update_fields=['status', 'updated_at'])
        return order


class PurchaseOrderItem(TimeStampedModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    purchase_request_item = models.ForeignKey(PurchaseRequestItem, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_order_items')
    description = models.CharField('Descrição', max_length=255)
    unit = models.CharField('Unidade', max_length=20)
    quantity = models.DecimalField('Quantidade', max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    unit_price = models.DecimalField('Preço unitário', max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])

    class Meta:
        verbose_name = 'Item da Ordem de Compra'
        verbose_name_plural = 'Itens da Ordem de Compra'
        ordering = ['created_at']

    def __str__(self):
        return self.description

    @property
    def total_price(self):
        return (self.quantity * self.unit_price).quantize(Decimal('0.01'))
