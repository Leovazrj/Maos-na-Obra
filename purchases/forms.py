from django import forms

from .models import PurchaseOrder, PurchaseOrderItem, PurchaseRequest, PurchaseRequestItem, Quotation, QuotationItemPrice, QuotationSupplier


class PurchaseRequestForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequest
        fields = ['project', 'title', 'status', 'notes']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título da solicitação'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações'}),
        }


class PurchaseRequestItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseRequestItem
        fields = ['input_item', 'description', 'unit', 'quantity', 'notes']
        widgets = {
            'input_item': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descrição do item'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unidade'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observações'}),
        }


class QuotationForm(forms.ModelForm):
    class Meta:
        model = Quotation
        fields = ['title', 'status', 'winner_supplier', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título da cotação'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'winner_supplier': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações'}),
        }


class QuotationSupplierForm(forms.ModelForm):
    class Meta:
        model = QuotationSupplier
        fields = ['supplier', 'status', 'notes']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observações'}),
        }


class QuotationItemPriceForm(forms.ModelForm):
    class Meta:
        model = QuotationItemPrice
        fields = ['quotation_supplier', 'purchase_request_item', 'unit_price', 'notes']
        widgets = {
            'quotation_supplier': forms.Select(attrs={'class': 'form-control'}),
            'purchase_request_item': forms.Select(attrs={'class': 'form-control'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observações'}),
        }


class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['purchase_request', 'quotation', 'supplier', 'title', 'status', 'notes']
        widgets = {
            'purchase_request': forms.Select(attrs={'class': 'form-control'}),
            'quotation': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título da ordem'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações'}),
        }


class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['purchase_request_item', 'description', 'unit', 'quantity', 'unit_price']
        widgets = {
            'purchase_request_item': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Descrição'}),
            'unit': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Unidade'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
        }
