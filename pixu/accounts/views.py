from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import RedirectView

from pixu.accounts.forms import AccountProfileForm
from pixu.accounts.models import PixProfile
from pixu.accounts.models import User


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.pk == self.request.user.pk:
            context["pix_profile"] = PixProfile.objects.filter(user=self.object).first()
        return context


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, FormView):
    form_class = AccountProfileForm
    template_name = "accounts/user_form.html"
    success_message = _("Perfil atualizado com sucesso.")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self) -> str:
        assert self.request.user.is_authenticated  # type guard
        return self.request.user.get_absolute_url()

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("accounts:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()
