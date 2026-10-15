from django.urls import path

from .views import CsvExtractExportView
from .views import PaidExtractView
from .views import PayableExtractView
from .views import PdfExtractExportView
from .views import ReceivableExtractView

app_name = "extracts"

urlpatterns = [
    path("payable/", PayableExtractView.as_view(), name="payable"),
    path("receivable/", ReceivableExtractView.as_view(), name="receivable"),
    path("paid/", PaidExtractView.as_view(), name="paid"),
    path("<str:kind>/export.csv", CsvExtractExportView.as_view(), name="export_csv"),
    path("<str:kind>/export.pdf", PdfExtractExportView.as_view(), name="export_pdf"),
]
