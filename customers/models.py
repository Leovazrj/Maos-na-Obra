from django.db import models
from django.conf import settings
from core.models import TimeStampedModel


class Customer(TimeStampedModel):
    PERSON_TYPE_CHOICES = [
        ('F', 'Pessoa Física'),
        ('J', 'Pessoa Jurídica'),
    ]

    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
    ]

    name = models.CharField('Nome/Razão Social', max_length=255)
    person_type = models.CharField('Tipo de Pessoa', max_length=1, choices=PERSON_TYPE_CHOICES, default='F')
    document_number = models.CharField('CPF/CNPJ', max_length=20, blank=True, null=True)
    email = models.EmailField('Email', blank=True, null=True)
    phone = models.CharField('Telefone', max_length=20, blank=True, null=True)
    address = models.TextField('Endereço', blank=True, null=True)
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='active')

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['name']

    def __str__(self):
        return self.name


class CustomerInteraction(TimeStampedModel):
    INTERACTION_TYPE_CHOICES = [
        ('call', 'Ligação'),
        ('email', 'Email'),
        ('meeting', 'Reunião'),
        ('whatsapp', 'WhatsApp'),
        ('other', 'Outro'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='interactions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='customer_interactions')
    interaction_type = models.CharField('Tipo de Interação', max_length=20, choices=INTERACTION_TYPE_CHOICES, default='call')
    interaction_date = models.DateField('Data da Interação')
    description = models.TextField('Descrição')

    class Meta:
        verbose_name = 'Interação com Cliente'
        verbose_name_plural = 'Interações com Clientes'
        ordering = ['-interaction_date', '-created_at']

    def __str__(self):
        return f'{self.get_interaction_type_display()} com {self.customer.name} em {self.interaction_date}'


class CustomerDocument(TimeStampedModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField('Título', max_length=255)
    file = models.FileField('Arquivo', upload_to='customer_documents/%Y/%m/')
    visible_in_portal = models.BooleanField('Visível no Portal do Cliente', default=False)

    class Meta:
        verbose_name = 'Documento do Cliente'
        verbose_name_plural = 'Documentos do Clientes'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class CustomerPhoto(TimeStampedModel):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='photos')
    title = models.CharField('Título', max_length=255)
    image = models.ImageField('Imagem', upload_to='customer_photos/%Y/%m/')
    visible_in_portal = models.BooleanField('Visível no Portal do Cliente', default=False)

    class Meta:
        verbose_name = 'Foto do Cliente'
        verbose_name_plural = 'Fotos do Cliente'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
