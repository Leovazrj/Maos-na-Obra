from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import views as auth_views
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.urls import reverse
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView

from .forms import ProfileForm, SignUpForm
from .models import User


class SignUpView(CreateView):
    model = User
    form_class = SignUpForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('dashboard:home')

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(self.request, 'Cadastro realizado com sucesso.')
        return response


class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = 'accounts/profile_form.html'
    success_url = reverse_lazy('dashboard:home')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Perfil atualizado com sucesso.')
        return super().form_valid(form)


class PasswordResetRequestView(auth_views.PasswordResetView):
    def form_valid(self, form):
        response = super().form_valid(form)
        email = form.cleaned_data.get('email', '').strip()
        try:
            user = get_user_model().objects.get(email__iexact=email, is_active=True)
        except get_user_model().DoesNotExist:
            self.request.session.pop('password_reset_link', None)
            return response

        if self._should_expose_reset_link():
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            self.request.session['password_reset_link'] = self.request.build_absolute_uri(
                reverse('accounts:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
            )
        else:
            self.request.session.pop('password_reset_link', None)
        return response

    def _should_expose_reset_link(self):
        from django.conf import settings

        return settings.DEBUG or settings.EMAIL_BACKEND != 'django.core.mail.backends.smtp.EmailBackend'


class PasswordResetDoneView(auth_views.PasswordResetDoneView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['password_reset_link'] = self.request.session.pop('password_reset_link', None)
        return context
