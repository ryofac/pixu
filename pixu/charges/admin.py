from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import path
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .forms import ChargeAbsoluteDeleteForm
from .models import Charge
from .models import ChargeDeletionAudit
from .services import absolutely_delete_charge


@admin.register(Charge)
class ChargeAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "creator", "state", "created_at", "delete_link")
    list_select_related = ("creator",)
    search_fields = ("title", "creator__username", "creator__email")
    list_filter = ("state", "created_at")

    def get_list_display(self, request):
        fields = super().get_list_display(request)
        if request.user.is_superuser:
            return fields
        return tuple(field for field in fields if field != "delete_link")

    def has_delete_permission(self, request, obj=None):
        # Django's generic delete views/actions bypass our audit and safeguards.
        return False

    def get_urls(self):
        custom_urls = [
            path(
                "<path:object_id>/absolute-delete/",
                self.admin_site.admin_view(self.absolute_delete_view),
                name="charges_charge_absolute_delete",
            ),
        ]
        return custom_urls + super().get_urls()

    @admin.display(description=_("Exclusão absoluta"))
    def delete_link(self, obj):
        url = reverse("admin:charges_charge_absolute_delete", args=[obj.pk])
        return format_html('<a href="{}">Excluir…</a>', url)

    def absolute_delete_view(self, request, object_id):
        if not request.user.is_superuser:
            raise PermissionDenied
        charge = get_object_or_404(Charge, pk=object_id)
        form = ChargeAbsoluteDeleteForm(request.POST or None)
        if request.method == "POST" and form.is_valid():
            try:
                absolutely_delete_charge(
                    charge_id=charge.pk,
                    actor=request.user,
                    reason=form.cleaned_data["reason"],
                )
            except PermissionDenied:
                raise
            except ValidationError as error:
                for message in error.messages:
                    form.add_error(None, message)
            else:
                self.message_user(
                    request,
                    _("A cobrança e seus dados vinculados foram excluídos."),
                    messages.SUCCESS,
                )
                return redirect("admin:charges_charge_changelist")

        context = {
            **self.admin_site.each_context(request),
            "title": _("Excluir cobrança definitivamente"),
            "opts": self.opts,
            "original": charge,
            "form": form,
        }
        return render(
            request,
            "admin/charges/charge/absolute_delete.html",
            context,
            status=400 if form.errors else 200,
        )


@admin.register(ChargeDeletionAudit)
class ChargeDeletionAuditAdmin(admin.ModelAdmin):
    list_display = ("charge_id_snapshot", "deleted_by", "deleted_at", "reason")
    list_select_related = ("deleted_by",)
    readonly_fields = ("charge_id_snapshot", "deleted_by", "deleted_at", "reason")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
