from django.urls import path, reverse_lazy

from .forms import EmailAuthenticationForm, UserPasswordChangeForm
from .views import (
    PasswordResetDoneView,
    PasswordResetRequestView,
    ProfileView,
    SignUpView,
)
from django.contrib.auth import views as auth_views

app_name = 'accounts'

urlpatterns = [
    path('cadastre-se/', SignUpView.as_view(), name='signup'),
    path(
        'login/',
        auth_views.LoginView.as_view(
            authentication_form=EmailAuthenticationForm,
            template_name='accounts/login.html',
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('perfil/', ProfileView.as_view(), name='profile'),
    path(
        'alterar-senha/',
        auth_views.PasswordChangeView.as_view(
            form_class=UserPasswordChangeForm,
            template_name='accounts/password_change_form.html',
            success_url=reverse_lazy('accounts:password_change_done'),
        ),
        name='password_change',
    ),
    path(
        'alterar-senha/sucesso/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='accounts/password_change_done.html'
        ),
        name='password_change_done',
    ),
    path(
        'esqueci-minha-senha/',
        PasswordResetRequestView.as_view(
            template_name='accounts/password_reset_form.html',
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
            success_url=reverse_lazy('accounts:password_reset_done')
        ),
        name='password_reset',
    ),
    path(
        'esqueci-minha-senha/sucesso/',
        PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_done',
    ),
    path(
        'esqueci-minha-senha/confirmar/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url=reverse_lazy('accounts:password_reset_complete')
        ),
        name='password_reset_confirm',
    ),
    path(
        'esqueci-minha-senha/completo/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete',
    ),
]
