from django.contrib import admin

from .models import AccountPayable, AccountReceivable, FinancialAppropriation, FinancialTransaction, InvoiceXml


class FinancialTransactionPayableInline(admin.TabularInline):
    model = FinancialTransaction
    fk_name = 'account_payable'
    extra = 0


class FinancialTransactionReceivableInline(admin.TabularInline):
    model = FinancialTransaction
    fk_name = 'account_receivable'
    extra = 0


class FinancialAppropriationInline(admin.TabularInline):
    model = FinancialAppropriation
    extra = 0


@admin.register(AccountPayable)
class AccountPayableAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'supplier', 'due_date', 'amount', 'status')
    list_filter = ('status', 'due_date')
    search_fields = ('title', 'supplier__legal_name', 'purchase_order__title')
    inlines = [FinancialTransactionPayableInline]


@admin.register(AccountReceivable)
class AccountReceivableAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'customer', 'due_date', 'amount', 'status', 'billing_type')
    list_filter = ('status', 'billing_type', 'due_date')
    search_fields = ('title', 'customer__name')
    inlines = [FinancialTransactionReceivableInline]


@admin.register(InvoiceXml)
class InvoiceXmlAdmin(admin.ModelAdmin):
    list_display = ('issuer_name', 'project', 'access_key', 'total_amount', 'imported_at')
    search_fields = ('issuer_name', 'access_key', 'project__name')
    inlines = [FinancialAppropriationInline]


@admin.register(FinancialAppropriation)
class FinancialAppropriationAdmin(admin.ModelAdmin):
    list_display = ('project', 'service_name', 'amount', 'percentage')
    search_fields = ('project__name', 'service_name')


@admin.register(FinancialTransaction)
class FinancialTransactionAdmin(admin.ModelAdmin):
    list_display = ('description', 'project', 'transaction_type', 'transaction_date', 'amount')
    list_filter = ('transaction_type', 'transaction_date')
    search_fields = ('description', 'project__name')
