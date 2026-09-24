import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="PixProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "pix_key",
                    models.CharField(blank=True, max_length=255, verbose_name="chave Pix principal"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="atualizado em"),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pix_profile",
                        to="accounts.user",
                        verbose_name="usuário",
                    ),
                ),
            ],
            options={
                "verbose_name": "perfil Pix",
                "verbose_name_plural": "perfis Pix",
            },
        ),
    ]
