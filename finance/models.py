from datetime import datetime
from decimal import Decimal

from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone

from core.models import TimeStampedModel


class AccountPayable(TimeStampedModel):
    STATUS_CHOICES = [
        ('open', 'Em aberto'),
        ('paid', 'Pago'),
        ('cancelled', 'Cancelado'),
    ]

    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='accounts_payable')
    supplier = models.ForeignKey('suppliers.Supplier', on_delete=models.PROTECT, related_name='accounts_payable')
    purchase_order = models.OneToOneField(
        'purchases.PurchaseOrder',
        on_delete=models.CASCADE,
        related_name='account_payable',
        null=True,
        blank=True,
    )
    title = models.CharField('Título', max_length=255)
    due_date = models.DateField('Vencimento')
    amount = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='open')
    source_label = models.CharField('Origem', max_length=255, default='Lançamento manual')
    notes = models.TextField('Observações', blank=True, null=True)
    paid_at = models.DateTimeField('Pago em', blank=True, null=True)

    class Meta:
        verbose_name = 'Conta a Pagar'
        verbose_name_plural = 'Contas a Pagar'
        ordering = ['due_date', '-created_at']

    def __str__(self):
        return self.title

    @property
    def origin_display(self):
        if self.purchase_order:
            return f'Ordem de compra {self.purchase_order.title}'
        return self.source_label

    @property
    def paid_value(self):
        total = self.transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return total.quantize(Decimal('0.01'))

    @property
    def open_value(self):
        remaining = self.amount - self.paid_value
        return max(remaining, Decimal('0.00')).quantize(Decimal('0.01'))

    def register_payment(self, transaction_date=None, notes=''):
        existing = self.transactions.order_by('-transaction_date', '-created_at').first()
        if self.status == 'paid' and existing:
            return existing

        transaction_date = transaction_date or timezone.localdate()
        if isinstance(transaction_date, str):
            transaction_date = datetime.fromisoformat(transaction_date).date()

        with transaction.atomic():
            movement = FinancialTransaction.objects.create(
                project=self.project,
                account_payable=self,
                transaction_type='outflow',
                transaction_date=transaction_date,
                amount=self.amount,
                description=self.title,
                notes=notes,
            )
            self.status = 'paid'
            self.paid_at = timezone.now()
            self.save(update_fields=['status', 'paid_at', 'updated_at'])
        return movement


class AccountReceivable(TimeStampedModel):
    STATUS_CHOICES = [
        ('open', 'Em aberto'),
        ('received', 'Recebido'),
        ('cancelled', 'Cancelado'),
    ]
    BILLING_TYPE_CHOICES = [
        ('admin', 'Administração de obra'),
        ('measurement', 'Medição física'),
        ('progress_fee', 'Taxa por avanço físico'),
        ('manual', 'Manual'),
    ]

    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='accounts_receivable')
    customer = models.ForeignKey('customers.Customer', on_delete=models.PROTECT, related_name='accounts_receivable')
    title = models.CharField('Título', max_length=255)
    due_date = models.DateField('Vencimento')
    amount = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    billing_type = models.CharField('Tipo de faturamento', max_length=20, choices=BILLING_TYPE_CHOICES, default='manual')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='open')
    source_label = models.CharField('Origem', max_length=255, default='Faturamento manual')
    notes = models.TextField('Observações', blank=True, null=True)
    received_at = models.DateTimeField('Recebido em', blank=True, null=True)

    class Meta:
        verbose_name = 'Conta a Receber'
        verbose_name_plural = 'Contas a Receber'
        ordering = ['due_date', '-created_at']

    def __str__(self):
        return self.title

    @property
    def origin_display(self):
        return self.source_label

    @property
    def received_value(self):
        total = self.transactions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return total.quantize(Decimal('0.01'))

    @property
    def open_value(self):
        remaining = self.amount - self.received_value
        return max(remaining, Decimal('0.00')).quantize(Decimal('0.01'))

    def register_receipt(self, transaction_date=None, notes=''):
        existing = self.transactions.order_by('-transaction_date', '-created_at').first()
        if self.status == 'received' and existing:
            return existing

        transaction_date = transaction_date or timezone.localdate()
        if isinstance(transaction_date, str):
            transaction_date = datetime.fromisoformat(transaction_date).date()

        with transaction.atomic():
            movement = FinancialTransaction.objects.create(
                project=self.project,
                account_receivable=self,
                transaction_type='inflow',
                transaction_date=transaction_date,
                amount=self.amount,
                description=self.title,
                notes=notes,
            )
            self.status = 'received'
            self.received_at = timezone.now()
            self.save(update_fields=['status', 'received_at', 'updated_at'])
        return movement


class InvoiceXml(TimeStampedModel):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='invoice_xmls')
    xml_file = models.FileField('XML original', upload_to='finance/invoices/')
    access_key = models.CharField('Chave de acesso', max_length=44, blank=True, null=True)
    issuer_name = models.CharField('Emitente', max_length=255, blank=True, null=True)
    total_amount = models.DecimalField('Valor total', max_digits=12, decimal_places=2, default=Decimal('0.00'))
    imported_at = models.DateTimeField('Importado em', auto_now_add=True)
    notes = models.TextField('Observações', blank=True, null=True)

    class Meta:
        verbose_name = 'NFe XML'
        verbose_name_plural = 'NFe XMLs'
        ordering = ['-imported_at', '-created_at']

    def __str__(self):
        return self.issuer_name or self.xml_file.name


class FinancialAppropriation(TimeStampedModel):
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='financial_appropriations')
    invoice_xml = models.ForeignKey(InvoiceXml, on_delete=models.CASCADE, related_name='appropriations', blank=True, null=True)
    service_name = models.CharField('Serviço', max_length=255)
    amount = models.DecimalField('Valor apropriado', max_digits=12, decimal_places=2)
    percentage = models.DecimalField('Percentual', max_digits=5, decimal_places=2, blank=True, null=True)
    notes = models.TextField('Observações', blank=True, null=True)

    class Meta:
        verbose_name = 'Apropriação Financeira'
        verbose_name_plural = 'Apropriações Financeiras'
        ordering = ['project__name', 'service_name', '-created_at']

    def __str__(self):
        return f'{self.project.name} - {self.service_name}'


class FinancialTransaction(TimeStampedModel):
    TYPE_CHOICES = [
        ('inflow', 'Entrada'),
        ('outflow', 'Saída'),
    ]

    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='financial_transactions', blank=True, null=True)
    account_payable = models.ForeignKey(
        AccountPayable,
        on_delete=models.CASCADE,
        related_name='transactions',
        blank=True,
        null=True,
    )
    account_receivable = models.ForeignKey(
        AccountReceivable,
        on_delete=models.CASCADE,
        related_name='transactions',
        blank=True,
        null=True,
    )
    transaction_type = models.CharField('Tipo', max_length=20, choices=TYPE_CHOICES)
    transaction_date = models.DateField('Data')
    amount = models.DecimalField('Valor', max_digits=12, decimal_places=2)
    description = models.CharField('Descrição', max_length=255)
    notes = models.TextField('Observações', blank=True, null=True)

    class Meta:
        verbose_name = 'Movimentação Financeira'
        verbose_name_plural = 'Movimentações Financeiras'
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        return self.description

    @property
    def signed_amount(self):
        if self.transaction_type == 'outflow':
            return -self.amount
        return self.amount
