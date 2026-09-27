from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class ChargeCreditorMigrationTests(TransactionTestCase):
    def test_existing_charge_keeps_creator_as_creditor_and_preserves_debt(self):
        previous = [("charges", "0001_initial")]
        current = [("charges", "0002_charge_creditor")]
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        executor.migrate(previous)
        try:
            apps = executor.loader.project_state(previous).apps
            user = apps.get_model("accounts", "User")
            creator = user.objects.create(username="creator")
            debtor = user.objects.create(username="debtor")
            charge = apps.get_model("charges", "Charge").objects.create(
                creator_id=creator.pk,
                title="Cobrança existente",
                total_cents=10000,
            )
            participation = apps.get_model("charges", "Participation").objects.create(
                charge_id=charge.pk,
                user_id=debtor.pk,
                share_cents=5000,
                state="ACCEPTED",
            )
            debt = apps.get_model("charges", "Debt").objects.create(
                participation_id=participation.pk,
                debtor_id=debtor.pk,
                creditor_id=creator.pk,
                original_cents=5000,
            )
            executor = MigrationExecutor(connection)
            executor.migrate(current)
            apps = executor.loader.project_state(current).apps
            migrated_charge = apps.get_model("charges", "Charge").objects.get(
                pk=charge.pk,
            )
            migrated_debt = apps.get_model("charges", "Debt").objects.get(pk=debt.pk)
            assert migrated_charge.creditor_id == creator.pk
            assert migrated_charge.creator_id == creator.pk
            assert migrated_debt.creditor_id == debt.creditor_id
            assert migrated_debt.original_cents == debt.original_cents
            assert migrated_debt.participation_id == participation.pk
        finally:
            MigrationExecutor(connection).migrate(latest)
