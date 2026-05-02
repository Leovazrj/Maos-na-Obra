from django import forms

from projects.models import Project, PhysicalMeasurement
from .models import AccountPayable, AccountReceivable, FinancialTransaction, FinancialAppropriation, InvoiceXml


class AccountPayableForm(forms.ModelForm):
    class Meta:
        model = AccountPayable
        fields = ['project', 'supplier', 'title', 'due_date', 'amount', 'status', 'source_label', 'notes']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'source_label': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AccountReceivableForm(forms.ModelForm):
    class Meta:
        model = AccountReceivable
        fields = ['project', 'customer', 'title', 'due_date', 'amount', 'billing_type', 'status', 'source_label', 'notes']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'billing_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'source_label': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class FinancialTransactionFilterForm(forms.Form):
    project = forms.ModelChoiceField(
        queryset=Project.objects.select_related('customer').all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    transaction_type = forms.ChoiceField(
        choices=[('', 'Todos'), *FinancialTransaction.TYPE_CHOICES],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))


class FinancialReceiptBillingForm(forms.Form):
    project = forms.ModelChoiceField(queryset=Project.objects.select_related('customer').all(), widget=forms.Select(attrs={'class': 'form-control'}))
    billing_type = forms.ChoiceField(
        choices=[
            ('admin', 'Administração de obra'),
            ('measurement', 'Medição física'),
            ('progress_fee', 'Taxa por avanço físico'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    title = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    amount = forms.DecimalField(required=False, min_value=0, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    measurement = forms.ModelChoiceField(
        queryset=PhysicalMeasurement.objects.select_related('project', 'task').all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
    )
    progress_percentage = forms.DecimalField(required=False, min_value=0, max_value=100, widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))

    def clean(self):
        cleaned = super().clean()
        billing_type = cleaned.get('billing_type')
        project = cleaned.get('project')
        measurement = cleaned.get('measurement')

        if project and project.customer_id is None:
            raise forms.ValidationError('Selecione uma obra com cliente vinculado.')

        if billing_type == 'measurement' and measurement and measurement.project_id != project.pk:
            raise forms.ValidationError('A medição selecionada deve pertencer à obra escolhida.')

        return cleaned


class InvoiceXmlUploadForm(forms.Form):
    project = forms.ModelChoiceField(queryset=Project.objects.select_related('customer').all(), widget=forms.Select(attrs={'class': 'form-control'}))
    xml_file = forms.FileField(widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))


class FinancialAppropriationForm(forms.ModelForm):
    class Meta:
        model = FinancialAppropriation
        fields = ['project', 'service_name', 'amount', 'percentage', 'notes']
        widgets = {
            'project': forms.Select(attrs={'class': 'form-control'}),
            'service_name': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
