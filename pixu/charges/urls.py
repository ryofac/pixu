from django.urls import path

from .views import AcceptParticipationView
from .views import ChargeCreatePreviewView
from .views import ChargeCreateView
from .views import GuestOptionsPreviewView
from .views import ChargeCancelView
from .views import ChargeDetailView
from .views import ChargeItemCreateView
from .views import ChargeListView
from .views import ChargeSharesUpdateView
from .views import CompensationApplyView
from .views import CompensationPreviewView
from .views import DeclineParticipationView
from .views import InviteListView
from .views import ReplaceParticipantView
from .guest_views import GuestEntryClosedView
from .guest_views import GuestEntryView
from .guest_views import GuestPersonalView
from .guest_views import GuestPaymentView
from .guest_views import GuestEntriesManageView

app_name = "charges"
urlpatterns = [
    path("guest/<int:pk>/<str:token>/", GuestEntryView.as_view(), name="guest_entry"),
    path("guest/<int:pk>/closed/", GuestEntryClosedView.as_view(), name="guest_entry_closed"),
    path(
        "guest/<int:pk>/<int:participation_id>/<str:code>/",
        GuestPersonalView.as_view(),
        name="guest_personal",
    ),
    path(
        "guest/participations/<int:participation_id>/<str:code>/pay/",
        GuestPaymentView.as_view(),
        name="guest_pay",
    ),
    path("<int:pk>/guest/entries/", GuestEntriesManageView.as_view(), name="guest_entries_manage"),
    path("", ChargeListView.as_view(), name="list"),
    path("new/", ChargeCreateView.as_view(), name="create"),
    path("new/preview/", ChargeCreatePreviewView.as_view(), name="preview"),
    path("new/guest-options/", GuestOptionsPreviewView.as_view(), name="guest_options_preview"),
    path("invites/", InviteListView.as_view(), name="invites"),
    path("<int:pk>/shares/", ChargeSharesUpdateView.as_view(), name="edit_shares"),
    path("<int:pk>/items/", ChargeItemCreateView.as_view(), name="add_item"),
    path("<int:pk>/cancel/", ChargeCancelView.as_view(), name="cancel"),
    path(
        "debts/<int:debt_id>/compensations/<int:reciprocal_debt_id>/preview/",
        CompensationPreviewView.as_view(),
        name="compensation_preview",
    ),
    path(
        "debts/<int:debt_id>/compensations/<int:reciprocal_debt_id>/apply/",
        CompensationApplyView.as_view(),
        name="compensation_apply",
    ),
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
