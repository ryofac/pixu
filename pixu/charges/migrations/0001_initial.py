import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations
from django.db import models
from django.db.models import Q


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Charge",
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
                ("title", models.CharField(max_length=120, verbose_name="título")),
                (
                    "description",
                    models.TextField(blank=True, max_length=1000, verbose_name="descrição"),
                ),
                (
                    "total_cents",
                    models.PositiveBigIntegerField(verbose_name="valor total em centavos"),
                ),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("AWAITING_ACCEPTANCE", "Aguardando aceite"),
                            ("ACTIVE", "Ativa"),
                        ],
                        default="AWAITING_ACCEPTANCE",
                        max_length=24,
                        verbose_name="estado",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="criada em",
                    ),
                ),
                ("locked_at", models.DateTimeField(blank=True, null=True, verbose_name="bloqueada em")),
                (
                    "creator",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_charges",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="criador e recebedor",
                    ),
                ),
            ],
            options={
                "verbose_name": "cobrança",
                "verbose_name_plural": "cobranças",
                "ordering": ["-created_at", "-pk"],
            },
        ),
        migrations.CreateModel(
            name="Participation",
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
                    "share_cents",
                    models.PositiveBigIntegerField(verbose_name="cota em centavos"),
                ),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pendente"),
                            ("ACCEPTED", "Aceita"),
                            ("DECLINED", "Recusada"),
                        ],
                        default="PENDING",
                        max_length=12,
                        verbose_name="estado do convite",
                    ),
                ),
                (
                    "invited_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="convidada em",
                    ),
                ),
                ("accepted_at", models.DateTimeField(blank=True, null=True, verbose_name="aceita em")),
                ("declined_at", models.DateTimeField(blank=True, null=True, verbose_name="recusada em")),
                (
                    "charge",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="participations",
                        to="charges.charge",
                        verbose_name="cobrança",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="charge_participations",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="participante",
                    ),
                ),
            ],
            options={
                "verbose_name": "participação",
                "verbose_name_plural": "participações",
                "ordering": ["user_id", "pk"],
            },
        ),
        migrations.CreateModel(
            name="Debt",
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
                    "original_cents",
                    models.PositiveBigIntegerField(verbose_name="valor original em centavos"),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        default=django.utils.timezone.now,
                        editable=False,
                        verbose_name="criada em",
                    ),
                ),
                (
                    "creditor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="debts_to_receive",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="recebedor",
                    ),
                ),
                (
                    "debtor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="debts_to_pay",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="devedor",
                    ),
                ),
                (
                    "participation",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="debt",
                        to="charges.participation",
                        verbose_name="participação aceita",
                    ),
                ),
            ],
            options={
                "verbose_name": "dívida",
                "verbose_name_plural": "dívidas",
                "ordering": ["-created_at", "-pk"],
            },
        ),
        migrations.AddConstraint(
            model_name="charge",
            constraint=models.CheckConstraint(
                condition=Q(("total_cents__gt", 0)),
                name="charge_total_positive",
            ),
        ),
        migrations.AddConstraint(
            model_name="charge",
            constraint=models.CheckConstraint(
                condition=Q(("state__in", ["AWAITING_ACCEPTANCE", "ACTIVE"])),
                name="charge_state_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="participation",
            constraint=models.UniqueConstraint(
                condition=~Q(("state", "DECLINED")),
                fields=("charge", "user"),
                name="one_current_participation_per_user",
            ),
        ),
        migrations.AddConstraint(
            model_name="participation",
            constraint=models.CheckConstraint(
                condition=Q(("share_cents__gte", 0)),
                name="participation_share_nonnegative",
            ),
        ),
        migrations.AddConstraint(
            model_name="participation",
            constraint=models.CheckConstraint(
                condition=Q(("state__in", ["PENDING", "ACCEPTED", "DECLINED"])),
                name="participation_state_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="debt",
            constraint=models.CheckConstraint(
                condition=Q(("original_cents__gte", 0)),
                name="debt_original_nonnegative",
            ),
        ),
        migrations.AddConstraint(
            model_name="debt",
            constraint=models.CheckConstraint(
                condition=~Q(("debtor", models.F("creditor"))),
                name="debt_parties_must_differ",
            ),
        ),
    ]
