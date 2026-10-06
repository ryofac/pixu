from django.db import migrations, models
from django.db.models import F, Q
from django.conf import settings


class Migration(migrations.Migration):
    dependencies = [
        ("settlements", "0004_pendingreceiptdeletion"),
    ]

    operations = [
        migrations.AlterField(
            model_name="payment",
            name="payer",
            field=models.ForeignKey(blank=True, null=True, on_delete=models.PROTECT, related_name="payments_made", to=settings.AUTH_USER_MODEL, verbose_name="pagador"),
        ),
        migrations.RemoveConstraint(
            model_name="payment",
            name="payment_parties_must_differ",
        ),
        migrations.AddConstraint(
            model_name="payment",
            constraint=models.CheckConstraint(condition=Q(("payer__isnull", True)) | ~Q(("payer", F("creditor"))), name="payment_parties_must_differ"),
        ),
    ]
