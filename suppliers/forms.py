from django import forms

from .models import Supplier, SupplierCategory


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = [
            'legal_name',
            'trade_name',
            'document_number',
            'email',
            'phone',
            'address',
            'categories',
            'notes',
            'status',
        ]
        widgets = {
            'legal_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Razão social ou nome'}),
            'trade_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome fantasia'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CNPJ ou CPF'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email para cotações'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefone'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Endereço completo'}),
            'categories': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações internas'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('status') == 'active' and not cleaned_data.get('email'):
            self.add_error('email', 'Fornecedores ativos precisam ter email para cotações.')
        return cleaned_data


class SupplierCategoryForm(forms.ModelForm):
    class Meta:
        model = SupplierCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da categoria'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição'}),
        }
