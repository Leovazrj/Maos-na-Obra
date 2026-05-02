from django.contrib import admin

from .models import (
    PurchaseOrder,
    PurchaseOrderItem,
    PurchaseRequest,
    PurchaseRequestItem,
    Quotation,
    QuotationItemPrice,
    QuotationSupplier,
)


class PurchaseRequestItemInline(admin.TabularInline):
    model = PurchaseRequestItem
    extra = 0


class QuotationSupplierInline(admin.TabularInline):
    model = QuotationSupplier
    extra = 0


class QuotationItemPriceInline(admin.TabularInline):
    model = QuotationItemPrice
    fk_name = 'quotation_supplier'
    extra = 0


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'status', 'total_items', 'created_at')
    list_filter = ('status',)
    search_fields = ('title', 'project__name')
    inlines = [PurchaseRequestItemInline]


@admin.register(PurchaseRequestItem)
class PurchaseRequestItemAdmin(admin.ModelAdmin):
    list_display = ('description', 'purchase_request', 'unit', 'quantity')
    search_fields = ('description', 'purchase_request__title')


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = ('title', 'purchase_request', 'status', 'winner_supplier', 'total_suppliers', 'total_value')
    list_filter = ('status',)
    search_fields = ('title', 'purchase_request__title')
    inlines = [QuotationSupplierInline]


@admin.register(QuotationSupplier)
class QuotationSupplierAdmin(admin.ModelAdmin):
    list_display = ('quotation', 'supplier', 'status', 'invited_at')
    list_filter = ('status',)
    search_fields = ('quotation__title', 'supplier__legal_name')
    inlines = [QuotationItemPriceInline]


@admin.register(QuotationItemPrice)
class QuotationItemPriceAdmin(admin.ModelAdmin):
    list_display = ('quotation_supplier', 'purchase_request_item', 'unit_price')
    search_fields = ('quotation_supplier__supplier__legal_name', 'purchase_request_item__description')


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('title', 'purchase_request', 'quotation', 'supplier', 'status', 'total_value')
    list_filter = ('status',)
    search_fields = ('title', 'purchase_request__title')
    inlines = [PurchaseOrderItemInline]


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'description', 'quantity', 'unit_price')
    search_fields = ('description', 'purchase_order__title')
