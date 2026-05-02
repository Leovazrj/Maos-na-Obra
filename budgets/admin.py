from django.contrib import admin

from .models import Budget, BudgetCompositionItem, BudgetItem, InputItem


class BudgetCompositionItemInline(admin.TabularInline):
    model = BudgetCompositionItem
    extra = 0


class BudgetItemInline(admin.TabularInline):
    model = BudgetItem
    extra = 0


@admin.register(InputItem)
class InputItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'unit_cost', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'project', 'budget_type', 'status', 'cost_total', 'sale_total', 'created_at')
    list_filter = ('budget_type', 'status')
    search_fields = ('name', 'project__name')
    inlines = [BudgetItemInline]


@admin.register(BudgetItem)
class BudgetItemAdmin(admin.ModelAdmin):
    list_display = ('budget', 'name', 'unit', 'quantity', 'cost_total', 'sale_total')
    search_fields = ('budget__name', 'name')
    inlines = [BudgetCompositionItemInline]


@admin.register(BudgetCompositionItem)
class BudgetCompositionItemAdmin(admin.ModelAdmin):
    list_display = ('budget_item', 'input_item', 'unit', 'quantity', 'unit_cost', 'cost_total')
    search_fields = ('budget_item__name', 'input_item__name')
