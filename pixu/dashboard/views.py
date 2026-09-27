from django.views.generic import TemplateView

from .services import dashboard_context


class HomeView(TemplateView):
    """Show a public introduction or the authenticated personal dashboard."""

    def get_template_names(self):
        if self.request.user.is_authenticated:
            return ["pages/dashboard.html"]
        return ["pages/landing.html"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context.update(dashboard_context(self.request.user))
        return context
