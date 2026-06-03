"""Quarterly reminder and liability helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from hub.db import Transaction


@dataclass(frozen=True, slots=True)
class Quarter:
    year: int
    number: int
    starts_on: date
    ends_on: date
    due_on: date

    def as_dict(self) -> dict[str, str | int]:
        return {
            "year": self.year,
            "number": self.number,
            "starts_on": self.starts_on.isoformat(),
            "ends_on": self.ends_on.isoformat(),
            "due_on": self.due_on.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class TaxEstimate:
    taxable_income_amd: Decimal
    tax_rate: Decimal
    estimated_tax_amd: Decimal

    def as_dict(self) -> dict[str, str]:
        return {
            "taxable_income_amd": str(self.taxable_income_amd),
            "tax_rate": str(self.tax_rate),
            "estimated_tax_amd": str(self.estimated_tax_amd),
        }


class TaxPlanner:
    """Calculate simple quarterly reminders and tax estimates."""

    def __init__(self, due_days_after_quarter: int = 20) -> None:
        self.due_days_after_quarter = due_days_after_quarter

    def quarters_for_year(self, year: int) -> tuple[Quarter, ...]:
        return tuple(self.quarter_for(date(year, month, 1)) for month in (1, 4, 7, 10))

    def quarter_for(self, value: date) -> Quarter:
        number = ((value.month - 1) // 3) + 1
        start_month = ((number - 1) * 3) + 1
        starts_on = date(value.year, start_month, 1)
        if number == 4:
            next_quarter = date(value.year + 1, 1, 1)
        else:
            next_quarter = date(value.year, start_month + 3, 1)
        ends_on = next_quarter - timedelta(days=1)
        due_on = ends_on + timedelta(days=self.due_days_after_quarter)
        return Quarter(
            year=value.year,
            number=number,
            starts_on=starts_on,
            ends_on=ends_on,
            due_on=due_on,
        )

    def estimate_liability(
        self,
        transactions: tuple[Transaction, ...],
        tax_rate: Decimal | str = Decimal("0.20"),
    ) -> TaxEstimate:
        rate = Decimal(str(tax_rate))
        income = Decimal("0")
        expense = Decimal("0")

        for transaction in transactions:
            amount_amd = self._amount_in_amd(transaction)
            if transaction.kind == "income":
                income += amount_amd
            elif transaction.kind == "expense":
                expense += amount_amd

        taxable = max(Decimal("0"), income - expense).quantize(Decimal("0.01"))
        tax = (taxable * rate).quantize(Decimal("0.01"))
        return TaxEstimate(
            taxable_income_amd=taxable,
            tax_rate=rate,
            estimated_tax_amd=tax,
        )

    def _amount_in_amd(self, transaction: Transaction) -> Decimal:
        if transaction.currency == "AMD":
            return transaction.amount
        if transaction.rate_to_amd is None:
            raise ValueError(f"missing AMD rate for {transaction.currency} transaction")
        return (transaction.amount * transaction.rate_to_amd).quantize(Decimal("0.01"))
