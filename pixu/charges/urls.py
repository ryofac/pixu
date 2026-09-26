from django.urls import path

from .views import AcceptParticipationView
from .views import ChargeCreatePreviewView
from .views import ChargeCreateView
from .views import ChargeDetailView
from .views import ChargeListView
from .views import ChargeSharesUpdateView
from .views import DeclineParticipationView
from .views import InviteListView
from .views import ReplaceParticipantView

app_name = "charges"
urlpatterns = [
    path("", ChargeListView.as_view(), name="list"),
    path("new/", ChargeCreateView.as_view(), name="create"),
    path("new/preview/", ChargeCreatePreviewView.as_view(), name="preview"),
    path("invites/", InviteListView.as_view(), name="invites"),
    path("<int:pk>/shares/", ChargeSharesUpdateView.as_view(), name="edit_shares"),
    path(
        "<int:pk>/participations/<int:participation_id>/replace/",
        ReplaceParticipantView.as_view(),
        name="replace_participant",
    ),
    path("<int:pk>/", ChargeDetailView.as_view(), name="detail"),
    path(
        "<int:pk>/participations/<int:participation_id>/accept/",
        AcceptParticipationView.as_view(),
        name="accept",
    ),
    path(
        "<int:pk>/participations/<int:participation_id>/decline/",
        DeclineParticipationView.as_view(),
        name="decline",
    ),
]
