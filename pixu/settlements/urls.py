from django.urls import path

from .views import ConfirmPaymentView
from .views import PaymentCreateView
from .views import PaymentReceiptDeleteView
from .views import PaymentReceiptUpdateView
from .views import PaymentReceiptView
from .views import RejectPaymentView

app_name = "settlements"

urlpatterns = [
    path("debts/<int:debt_id>/pay/", PaymentCreateView.as_view(), name="record"),
    path(
        "payments/<int:payment_id>/confirm/",
        ConfirmPaymentView.as_view(),
        name="confirm",
    ),
    path(
        "payments/<int:payment_id>/reject/",
        RejectPaymentView.as_view(),
        name="reject",
    ),
    path(
        "payments/<int:payment_id>/receipt/",
        PaymentReceiptView.as_view(),
        name="receipt",
    ),
    path(
        "payments/<int:payment_id>/receipt/update/",
        PaymentReceiptUpdateView.as_view(),
        name="receipt_update",
    ),
    path(
        "payments/<int:payment_id>/receipt/delete/",
        PaymentReceiptDeleteView.as_view(),
        name="receipt_delete",
    ),
]
