from django.conf import settings
from django.db import migrations
from django.db import models
import django.db.models.deletion


def copy_creator_to_creditor(apps, schema_editor):
    charge = apps.get_model("charges", "Charge")
    charge.objects.using(schema_editor.connection.alias).update(
        creditor_id=models.F("creator_id"),
    )


class Migration(migrations.Migration):
    dependencies = [
        ("charges", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="charge",
            name="creator",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="created_charges",
                to=settings.AUTH_USER_MODEL,
                verbose_name="criador",
            ),
        ),
        migrations.AddField(
            model_name="charge",
            name="creditor",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="receivable_charges",
                to=settings.AUTH_USER_MODEL,
                verbose_name="recebedor",
            ),
        ),
        migrations.RunPython(copy_creator_to_creditor, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="charge",
            name="creditor",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="receivable_charges",
                to=settings.AUTH_USER_MODEL,
                verbose_name="recebedor",
            ),
        ),
    ]
