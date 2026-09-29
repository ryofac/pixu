from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse


class OnboardingMiddleware:
    """Keep new accounts in onboarding until their profile is confirmed."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and not user.onboarding_completed:
            onboarding_path = reverse("accounts:onboarding")
            exempt_prefixes = ["/accounts/", onboarding_path]
            exempt_prefixes.extend(
                prefix
                for prefix in (settings.STATIC_URL, settings.MEDIA_URL)
                if prefix
            )
            exempt_request = any(
                request.path_info.startswith(prefix) for prefix in exempt_prefixes
            )
            if not exempt_request:
                if request.headers.get("HX-Request") == "true":
                    response = HttpResponse(status=204)
                    response["HX-Redirect"] = onboarding_path
                    return response
                return redirect("accounts:onboarding")
        return self.get_response(request)
