from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("charges", "0008_debt_auto_confirm_payments"),
        ("settlements", "0005_guest_payments"),
    ]

    operations = [
        migrations.AddField(
            model_name="payment",
            name="confirmation_source",
            field=models.CharField(
                choices=[("MANUAL", "Manual"), ("AUTOMATIC", "Automática")],
                default="MANUAL",
                max_length=12,
                verbose_name="origem da confirmação",
            ),
        ),
    ]
