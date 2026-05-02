from django.contrib import admin

from .models import ClientPortalAccess


@admin.register(ClientPortalAccess)
class ClientPortalAccessAdmin(admin.ModelAdmin):
    list_display = ('customer', 'user', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('customer__name', 'user__name', 'user__email')
