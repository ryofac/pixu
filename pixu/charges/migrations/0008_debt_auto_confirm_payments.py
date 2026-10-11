from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("charges", "0007_charge_guest_total_participants"),
    ]

    operations = [
        migrations.AddField(
            model_name="debt",
            name="auto_confirm_payments",
            field=models.BooleanField(
                default=False,
                verbose_name="confirmar pagamentos declarados automaticamente",
            ),
        ),
    ]
