from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_user_onboarding_completed"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="allow_direct_charge_inclusion",
            field=models.BooleanField(
                default=False,
                verbose_name="permitir inclusão direta em cobranças",
            ),
        ),
    ]
