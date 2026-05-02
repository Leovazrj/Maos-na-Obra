from django.db import models

from core.models import TimeStampedModel


class ClientPortalAccess(TimeStampedModel):
    customer = models.ForeignKey('customers.Customer', on_delete=models.CASCADE, related_name='portal_accesses')
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        related_name='client_portal_accesses',
        blank=True,
        null=True,
    )
    is_active = models.BooleanField('Ativo', default=True)
    notes = models.TextField('Observações', blank=True, null=True)

    class Meta:
        verbose_name = 'Acesso ao Portal do Cliente'
        verbose_name_plural = 'Acessos ao Portal do Cliente'
        ordering = ['customer__name', 'user__name']
        constraints = [
            models.UniqueConstraint(fields=['customer', 'user'], name='unique_client_portal_access'),
        ]

    def __str__(self):
        user_label = self.user.name if self.user else 'Sem usuário'
        return f'{user_label} - {self.customer.name}'
