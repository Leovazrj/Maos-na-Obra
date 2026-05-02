from django.core.exceptions import ValidationError
from django.db import models

from core.models import TimeStampedModel


class SupplierCategory(TimeStampedModel):
    name = models.CharField('Nome', max_length=120, unique=True)
    description = models.TextField('Descrição', blank=True, null=True)

    class Meta:
        verbose_name = 'Categoria de Fornecedor'
        verbose_name_plural = 'Categorias de Fornecedores'
        ordering = ['name']

    def __str__(self):
        return self.name


class Supplier(TimeStampedModel):
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
    ]

    legal_name = models.CharField('Razão Social ou Nome', max_length=255)
    trade_name = models.CharField('Nome Fantasia', max_length=255, blank=True, null=True)
    document_number = models.CharField('CNPJ/CPF', max_length=20, blank=True, null=True)
    email = models.EmailField('Email', blank=True, null=True)
    phone = models.CharField('Telefone', max_length=20, blank=True, null=True)
    address = models.TextField('Endereço', blank=True, null=True)
    categories = models.ManyToManyField(
        SupplierCategory,
        verbose_name='Categorias de fornecimento',
        related_name='suppliers',
        blank=True,
    )
    notes = models.TextField('Observações', blank=True, null=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='active')

    class Meta:
        verbose_name = 'Fornecedor'
        verbose_name_plural = 'Fornecedores'
        ordering = ['legal_name']

    def __str__(self):
        return self.legal_name

    @property
    def is_available_for_online_quote(self):
        return self.status == 'active' and bool(self.email)

    def clean(self):
        super().clean()
        if self.status == 'active' and not self.email:
            raise ValidationError({'email': 'Fornecedores ativos precisam ter email para cotações.'})
