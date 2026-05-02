from django import forms

from .models import Budget, BudgetCompositionItem, BudgetItem, InputItem


class InputItemForm(forms.ModelForm):
    class Meta:
        model = InputItem
        fields = ['name', 'unit', 'unit_cost', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do insumo'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'm², m³, kg, un...'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição do insumo'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BudgetForm(forms.ModelForm):
    class Meta:
        model = Budget
        fields = ['project', 'name', 'budget_type', 'margin_percentage', 'status', 'notes']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do orçamento'}),
            'budget_type': forms.Select(attrs={'class': 'form-control'}),
            'margin_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações'}),
        }


class BudgetItemForm(forms.ModelForm):
    class Meta:
        model = BudgetItem
        fields = ['name', 'unit', 'quantity', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Serviço ou item do orçamento'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unidade'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descrição'}),
        }


class BudgetCompositionItemForm(forms.ModelForm):
    class Meta:
        model = BudgetCompositionItem
        fields = ['input_item', 'unit', 'quantity', 'unit_cost']
        widgets = {
            'input_item': forms.Select(attrs={'class': 'form-control'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unidade'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }
