from django import forms
from .models import Customer, CustomerInteraction, CustomerDocument, CustomerPhoto

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'person_type', 'document_number', 'email', 'phone', 'address', 'status']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome ou Razão Social'}),
            'person_type': forms.Select(attrs={'class': 'form-control'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CPF ou CNPJ'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefone'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Endereço Completo'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }


class CustomerInteractionForm(forms.ModelForm):
    class Meta:
        model = CustomerInteraction
        fields = ['interaction_type', 'interaction_date', 'description']
        widgets = {
            'interaction_type': forms.Select(attrs={'class': 'form-control'}),
            'interaction_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Detalhes da interação'}),
        }


class CustomerDocumentForm(forms.ModelForm):
    class Meta:
        model = CustomerDocument
        fields = ['title', 'file', 'visible_in_portal']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título do documento'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'visible_in_portal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CustomerPhotoForm(forms.ModelForm):
    class Meta:
        model = CustomerPhoto
        fields = ['title', 'image', 'visible_in_portal']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título da foto'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'visible_in_portal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
