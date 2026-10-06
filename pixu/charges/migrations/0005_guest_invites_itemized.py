import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models
from django.db.models import F, Q


def copy_existing_shares_to_base(apps, schema_editor):
    apps.get_model("charges", "Participation").objects.update(
        base_share_cents=F("share_cents"),
    )


class Migration(migrations.Migration):
    dependencies = [
        ("charges", "0004_chargedeletionaudit"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="charge",
            name="guest_invites_enabled",
            field=models.BooleanField(default=False, verbose_name="entradas anônimas habilitadas"),
        ),
        migrations.AddField(
            model_name="charge",
            name="guest_entry_limit",
            field=models.PositiveSmallIntegerField(default=10, verbose_name="limite de entradas convidadas"),
        ),
        migrations.AddField(
            model_name="charge",
            name="guest_access_ttl_days",
            field=models.PositiveSmallIntegerField(default=7, verbose_name="validade do acesso convidado em dias"),
        ),
        migrations.AddField(
            model_name="charge",
            name="guest_entries_open",
            field=models.BooleanField(default=False, verbose_name="entradas convidadas abertas"),
        ),
        migrations.AddField(
            model_name="charge",
            name="guest_entries_closed_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="entradas fechadas em"),
        ),
        migrations.AddField(
            model_name="charge",
            name="guest_entry_token_digest",
            field=models.CharField(blank=True, max_length=64, verbose_name="digest do link convidado"),
        ),
        migrations.AddField(
            model_name="charge",
            name="guest_entry_code_digest",
            field=models.CharField(blank=True, max_length=64, verbose_name="digest do código convidado"),
        ),
        migrations.AddField(
            model_name="charge",
            name="guest_entry_token_created_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="link convidado criado em"),
        ),
        migrations.AddField(
            model_name="charge",
            name="guest_entry_token_revoked_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="link convidado revogado em"),
        ),
        migrations.AddField(
            model_name="participation",
            name="base_share_cents",
            field=models.PositiveBigIntegerField(default=0, verbose_name="parcela da base comum em centavos"),
        ),
        migrations.RunPython(
            copy_existing_shares_to_base,
            migrations.RunPython.noop,
        ),
        migrations.AddField(
            model_name="participation",
            name="guest_name",
            field=models.CharField(blank=True, max_length=120, null=True, verbose_name="nome autodeclarado do convidado"),
        ),
        migrations.AddField(
            model_name="participation",
            name="guest_name_normalized",
            field=models.CharField(blank=True, max_length=120, null=True, verbose_name="nome convidado normalizado"),
        ),
        migrations.AddField(
            model_name="participation",
            name="guest_access_digest",
            field=models.CharField(blank=True, max_length=64, verbose_name="digest do código pessoal"),
        ),
        migrations.AddField(
            model_name="participation",
            name="guest_access_created_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="código pessoal criado em"),
        ),
        migrations.AddField(
            model_name="participation",
            name="guest_access_expires_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="código pessoal expira em"),
        ),
        migrations.AddField(
            model_name="participation",
            name="guest_claimed_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="entrada convidada em"),
        ),
        migrations.AlterField(
            model_name="participation",
            name="user",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="charge_participations", to=settings.AUTH_USER_MODEL, verbose_name="participante"),
        ),
        migrations.AlterField(
            model_name="debt",
            name="debtor",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="debts_to_pay", to=settings.AUTH_USER_MODEL, verbose_name="devedor"),
        ),
        migrations.CreateModel(
            name="ChargeItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("description", models.CharField(max_length=160, verbose_name="descrição")),
                ("amount_cents", models.PositiveBigIntegerField(verbose_name="valor em centavos")),
                ("created_at", models.DateTimeField(default=django.utils.timezone.now, editable=False, verbose_name="criado em")),
                ("charge", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="charges.charge", verbose_name="cobrança")),
                ("participation", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="items", to="charges.participation", verbose_name="responsável")),
            ],
            options={
                "verbose_name": "item da cobrança",
                "verbose_name_plural": "itens da cobrança",
                "ordering": ["pk"],
            },
        ),
        migrations.AddConstraint(
            model_name="charge",
            constraint=models.CheckConstraint(condition=Q(("guest_entry_limit__gte", 1), ("guest_entry_limit__lte", 100)), name="guest_entry_limit_valid"),
        ),
        migrations.AddConstraint(
            model_name="charge",
            constraint=models.CheckConstraint(condition=Q(("guest_access_ttl_days__gte", 1), ("guest_access_ttl_days__lte", 30)), name="guest_access_ttl_valid"),
        ),
        migrations.AddConstraint(
            model_name="participation",
            constraint=models.CheckConstraint(condition=Q(("user__isnull", False), ("guest_name__isnull", True)) | Q(("user__isnull", True), ("guest_name__isnull", False)), name="participation_single_identity"),
        ),
        migrations.AddConstraint(
            model_name="chargeitem",
            constraint=models.CheckConstraint(condition=Q(("amount_cents__gt", 0)), name="charge_item_amount_positive"),
        ),
    ]
