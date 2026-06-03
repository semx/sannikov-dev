from datetime import date
from decimal import Decimal
from unittest import TestCase

from hub.db import Transaction
from hub.taxes import TaxPlanner


class TaxPlannerTest(TestCase):
    def test_builds_quarter_boundaries(self) -> None:
        quarter = TaxPlanner().quarter_for(date(2026, 5, 12))

        self.assertEqual(quarter.number, 2)
        self.assertEqual(quarter.starts_on.isoformat(), "2026-04-01")
        self.assertEqual(quarter.ends_on.isoformat(), "2026-06-30")
        self.assertEqual(quarter.due_on.isoformat(), "2026-07-20")

    def test_estimates_liability_in_amd(self) -> None:
        transactions = (
            Transaction(
                id=1,
                posted_on="2026-01-10",
                amount=Decimal("1000.00"),
                currency="USD",
                kind="income",
                rate_to_amd=Decimal("400.00"),
            ),
            Transaction(
                id=2,
                posted_on="2026-01-11",
                amount=Decimal("50000.00"),
                currency="AMD",
                kind="expense",
            ),
        )

        estimate = TaxPlanner().estimate_liability(transactions, tax_rate="0.20")

        self.assertEqual(estimate.taxable_income_amd, Decimal("350000.00"))
        self.assertEqual(estimate.estimated_tax_amd, Decimal("70000.00"))
