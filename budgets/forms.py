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
    input_item = forms.CharField(
        label='Insumo',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Digite o nome do insumo',
        }),
    )

    class Meta:
        model = BudgetCompositionItem
        fields = ['unit', 'quantity', 'unit_cost']
        widgets = {
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unidade'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }

    def clean_input_item(self):
        value = self.cleaned_data['input_item'].strip()
        if not value:
            raise forms.ValidationError('Informe o nome do insumo.')
        return value

    def save(self, commit=True):
        instance = super().save(commit=False)
        input_item_name = self.cleaned_data['input_item']
        input_item = InputItem.objects.filter(name__iexact=input_item_name).first()
        if input_item is None:
            input_item = InputItem.objects.create(
                name=input_item_name,
                unit=self.cleaned_data['unit'],
                unit_cost=self.cleaned_data['unit_cost'],
            )
        instance.input_item = input_item
        if commit:
            instance.save()
        return instance
