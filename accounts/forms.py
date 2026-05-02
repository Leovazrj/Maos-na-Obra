from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.password_validation import validate_password

from .models import User


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'seu@email.com',
                'autocomplete': 'email',
            }
        ),
    )

    password = forms.CharField(
        label='Senha',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Sua senha',
                'autocomplete': 'current-password',
            }
        ),
    )


class SignUpForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Senha',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Crie uma senha',
                'autocomplete': 'new-password',
            }
        ),
    )
    password2 = forms.CharField(
        label='Confirmação de senha',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Repita a senha',
                'autocomplete': 'new-password',
            }
        ),
    )

    class Meta:
        model = User
        fields = ('name', 'email')
        labels = {
            'name': 'Nome',
            'email': 'Email',
        }
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Seu nome',
                    'autocomplete': 'name',
                }
            ),
            'email': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'seu@email.com',
                    'autocomplete': 'email',
                }
            ),
        }

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        validate_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'As senhas não conferem.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])

        if commit:
            user.save()

        return user


class UserAdminCreationForm(SignUpForm):
    class Meta(SignUpForm.Meta):
        model = User
        fields = ('name', 'email')


class UserAdminChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField(label='Senha')

    class Meta:
        model = User
        fields = (
            'email',
            'name',
            'password',
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions',
        )
