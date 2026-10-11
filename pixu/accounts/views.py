from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import FormView
from django.views.generic import RedirectView

from pixu.accounts.forms import AccountProfileForm
from pixu.accounts.forms import OnboardingForm
from pixu.accounts.models import PixProfile
from pixu.accounts.models import User
from pixu.charges.models import Charge


def _charges_shared_with(user, other_user):
    visible_to_user = Q(creator=user) | Q(creditor=user) | Q(participations__user=user)
    visible_to_other = (
        Q(creator=other_user)
        | Q(creditor=other_user)
        | Q(participations__user=other_user)
    )
    return (
        Charge.objects.filter(visible_to_user)
        .filter(visible_to_other)
        .only("pk", "title", "state")
        .distinct()
        .order_by("-created_at", "-pk")
    )


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pix_profile"] = PixProfile.objects.filter(user=self.object).first()
        if self.object.pk == self.request.user.pk:
            context["is_own_profile"] = True
        else:
            context["is_own_profile"] = False
            context["shared_charges"] = _charges_shared_with(
                self.request.user,
                self.object,
            )
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


class OnboardingView(LoginRequiredMixin, FormView):
    form_class = OnboardingForm
    template_name = "accounts/onboarding.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and request.user.onboarding_completed:
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("home")


onboarding_view = OnboardingView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    permanent = False

    def get_redirect_url(self) -> str:
        return reverse("home")


user_redirect_view = UserRedirectView.as_view()
