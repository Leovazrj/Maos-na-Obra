from django import forms

from .models import DailyLog, PhysicalMeasurement, Project, ProjectTask


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name',
            'customer',
            'address',
            'expected_start_date',
            'expected_end_date',
            'status',
            'expected_value',
            'responsible',
            'description',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome da obra'}),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Endereço completo'}),
            'expected_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expected_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'expected_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'responsible': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição da obra'}),
        }


class DailyLogForm(forms.ModelForm):
    class Meta:
        model = DailyLog
        fields = ['log_date', 'weather', 'team_present', 'services_performed', 'occurrences', 'notes']
        widgets = {
            'log_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'weather': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Clima do dia'}),
            'team_present': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Equipe presente'}),
            'services_performed': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Serviços executados'}),
            'occurrences': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Ocorrências'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observações'}),
        }


class ProjectTaskForm(forms.ModelForm):
    class Meta:
        model = ProjectTask
        fields = ['name', 'planned_start_date', 'planned_end_date', 'planned_percentage', 'planned_cost', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Serviço ou etapa'}),
            'planned_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'planned_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'planned_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'planned_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Descrição da tarefa'}),
        }


class PhysicalMeasurementForm(forms.ModelForm):
    class Meta:
        model = PhysicalMeasurement
        fields = ['task', 'measurement_date', 'measured_percentage', 'measured_value', 'visible_in_portal', 'notes']
        widgets = {
            'task': forms.Select(attrs={'class': 'form-control'}),
            'measurement_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'measured_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'measured_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'visible_in_portal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Observações da medição'}),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)
        if project is not None:
            self.fields['task'].queryset = project.tasks.all()
