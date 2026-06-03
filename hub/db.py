"""SQLite persistence for transactions and generated invoices."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any


VALID_KINDS = {"income", "expense"}


@dataclass(frozen=True, slots=True)
class Transaction:
    id: int
    posted_on: str
    amount: Decimal
    currency: str
    kind: str
    note: str = ""
    counterparty: str = ""
    rate_to_amd: Decimal | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "posted_on": self.posted_on,
            "amount": str(self.amount),
            "currency": self.currency,
            "kind": self.kind,
            "note": self.note,
            "counterparty": self.counterparty,
            "rate_to_amd": str(self.rate_to_amd) if self.rate_to_amd is not None else None,
        }


class HubDatabase:
    """Thin repository around the SQLite database."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row

    def init_schema(self) -> None:
        self.connection.execute(
            """
            create table if not exists transactions (
              id integer primary key autoincrement,
              posted_on text not null,
              amount text not null,
              currency text not null,
              kind text not null check(kind in ('income', 'expense')),
              note text not null default '',
              counterparty text not null default '',
              rate_to_amd text
            )
            """
        )
        self.connection.execute(
            """
            create table if not exists invoices (
              id integer primary key autoincrement,
              invoice_number text not null unique,
              issued_on text not null,
              client_name text not null,
              currency text not null,
              total text not null,
              status text not null default 'draft'
            )
            """
        )
        self.connection.commit()

    def add_transaction(
        self,
        amount: Decimal | str | float,
        currency: str,
        kind: str,
        posted_on: str | None = None,
        note: str = "",
        counterparty: str = "",
        rate_to_amd: Decimal | str | float | None = None,
    ) -> Transaction:
        if kind not in VALID_KINDS:
            raise ValueError(f"invalid transaction kind: {kind}")

        parsed_amount = self._decimal(amount)
        if parsed_amount <= 0:
            raise ValueError("amount must be positive")

        parsed_date = posted_on or date.today().isoformat()
        currency_code = currency.upper()
        parsed_rate = self._decimal(rate_to_amd) if rate_to_amd is not None else None

        cursor = self.connection.execute(
            """
            insert into transactions (
              posted_on, amount, currency, kind, note, counterparty, rate_to_amd
            ) values (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                parsed_date,
                str(parsed_amount),
                currency_code,
                kind,
                note,
                counterparty,
                str(parsed_rate) if parsed_rate is not None else None,
            ),
        )
        self.connection.commit()
        return Transaction(
            id=int(cursor.lastrowid),
            posted_on=parsed_date,
            amount=parsed_amount,
            currency=currency_code,
            kind=kind,
            note=note,
            counterparty=counterparty,
            rate_to_amd=parsed_rate,
        )

    def list_transactions(
        self,
        kind: str | None = None,
        currency: str | None = None,
    ) -> tuple[Transaction, ...]:
        clauses: list[str] = []
        params: list[str] = []
        if kind is not None:
            clauses.append("kind = ?")
            params.append(kind)
        if currency is not None:
            clauses.append("currency = ?")
            params.append(currency.upper())

        where = f" where {' and '.join(clauses)}" if clauses else ""
        rows = self.connection.execute(
            f"select * from transactions{where} order by posted_on desc, id desc",
            params,
        ).fetchall()
        return tuple(self._transaction_from_row(row) for row in rows)

    def totals_by_currency(self) -> dict[str, dict[str, Decimal]]:
        rows = self.connection.execute("select currency, kind, amount from transactions").fetchall()
        totals: dict[str, dict[str, Decimal]] = {}
        for row in rows:
            currency = row["currency"]
            totals.setdefault(currency, {"income": Decimal("0"), "expense": Decimal("0")})
            totals[currency][row["kind"]] += self._decimal(row["amount"])
        return totals

    def close(self) -> None:
        self.connection.close()

    def _transaction_from_row(self, row: sqlite3.Row) -> Transaction:
        rate = row["rate_to_amd"]
        return Transaction(
            id=row["id"],
            posted_on=row["posted_on"],
            amount=self._decimal(row["amount"]),
            currency=row["currency"],
            kind=row["kind"],
            note=row["note"],
            counterparty=row["counterparty"],
            rate_to_amd=self._decimal(rate) if rate is not None else None,
        )

    def _decimal(self, value: Decimal | str | float | int) -> Decimal:
        return Decimal(str(value)).quantize(Decimal("0.01"))
