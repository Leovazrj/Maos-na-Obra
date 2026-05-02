from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View


class PostDeleteView(LoginRequiredMixin, View):
    model = None
    lookup_url_kwarg = 'pk'
    success_url = None
    success_message = ''

    def get_object(self):
        if self.model is None:
            raise AttributeError('Defina model na view de exclusão.')
        return get_object_or_404(self.model, pk=self.kwargs[self.lookup_url_kwarg])

    def get_success_url(self):
        if callable(self.success_url):
            return self.success_url(self)
        if self.success_url is None:
            raise AttributeError('Defina success_url na view de exclusão.')
        return self.success_url

    def delete_object(self, obj):
        return obj.delete()

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        label = str(obj)
        self.delete_object(obj)
        if self.success_message:
            messages.success(request, self.success_message.format(obj=label))
        return redirect(self.get_success_url())
