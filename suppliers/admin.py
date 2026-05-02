from django.contrib import admin

from .models import Supplier, SupplierCategory


@admin.register(SupplierCategory)
class SupplierCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('legal_name', 'trade_name', 'document_number', 'email', 'phone', 'status', 'created_at')
    list_filter = ('status', 'categories')
    search_fields = ('legal_name', 'trade_name', 'document_number', 'email')
    filter_horizontal = ('categories',)
