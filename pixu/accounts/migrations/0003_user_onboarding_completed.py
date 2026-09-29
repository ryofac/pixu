from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_pixprofile"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="onboarding_completed",
            field=models.BooleanField(default=True, verbose_name="onboarding concluído"),
        ),
    ]
