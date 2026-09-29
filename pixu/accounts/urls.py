from django.urls import path

from .views import onboarding_view
from .views import user_detail_view
from .views import user_redirect_view
from .views import user_update_view

app_name = "accounts"
urlpatterns = [
    path("~onboarding/", view=onboarding_view, name="onboarding"),
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
]
