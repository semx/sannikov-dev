from decimal import Decimal
from unittest import TestCase

from hub.db import HubDatabase


class HubDatabaseTest(TestCase):
    def test_adds_and_lists_transactions(self) -> None:
        database = HubDatabase()
        database.init_schema()
        database.add_transaction(
            amount="2500",
            currency="usd",
            kind="income",
            posted_on="2026-01-10",
            note="invoice",
            rate_to_amd="405.50",
        )
        database.add_transaction(
            amount="125",
            currency="USD",
            kind="expense",
            posted_on="2026-01-11",
        )

        transactions = database.list_transactions(currency="usd")
        totals = database.totals_by_currency()

        self.assertEqual(len(transactions), 2)
        self.assertEqual(transactions[0].currency, "USD")
        self.assertEqual(totals["USD"]["income"], Decimal("2500.00"))
        self.assertEqual(totals["USD"]["expense"], Decimal("125.00"))
        database.close()

    def test_rejects_invalid_transaction_kind(self) -> None:
        database = HubDatabase()
        database.init_schema()

        with self.assertRaises(ValueError):
            database.add_transaction(amount="10", currency="USD", kind="refund")

        database.close()
