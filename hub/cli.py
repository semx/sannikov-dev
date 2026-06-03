"""Command line interface for local operations."""

from __future__ import annotations

import argparse
import json
from decimal import Decimal
from pathlib import Path

from hub.db import HubDatabase
from hub.invoices import Invoice, InvoiceRenderer
from hub.taxes import TaxPlanner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="sannikov-hub", description="Personal automation toolkit")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_db = subparsers.add_parser("init-db", help="Initialize a SQLite database")
    init_db.add_argument("db_path")

    add = subparsers.add_parser("add-transaction", help="Add a transaction")
    add.add_argument("db_path")
    add.add_argument("--amount", required=True)
    add.add_argument("--currency", required=True)
    add.add_argument("--kind", required=True, choices=("income", "expense"))
    add.add_argument("--posted-on")
    add.add_argument("--note", default="")
    add.add_argument("--counterparty", default="")
    add.add_argument("--rate-to-amd")

    transactions = subparsers.add_parser("transactions", help="List transactions")
    transactions.add_argument("db_path")
    transactions.add_argument("--pretty", action="store_true")

    tax = subparsers.add_parser("tax-estimate", help="Estimate tax liability")
    tax.add_argument("db_path")
    tax.add_argument("--rate", default="0.20")
    tax.add_argument("--pretty", action="store_true")

    invoice = subparsers.add_parser("render-invoice", help="Render invoice JSON to HTML")
    invoice.add_argument("invoice_json")
    invoice.add_argument("output_html")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-db":
        database = HubDatabase(args.db_path)
        database.init_schema()
        database.close()
        print(json.dumps({"db_path": args.db_path, "status": "ready"}))
        return 0

    if args.command == "add-transaction":
        database = _open_db(args.db_path)
        transaction = database.add_transaction(
            amount=args.amount,
            currency=args.currency,
            kind=args.kind,
            posted_on=args.posted_on,
            note=args.note,
            counterparty=args.counterparty,
            rate_to_amd=args.rate_to_amd,
        )
        database.close()
        print(json.dumps(transaction.as_dict(), sort_keys=True))
        return 0

    if args.command == "transactions":
        database = _open_db(args.db_path)
        payload = {"transactions": [item.as_dict() for item in database.list_transactions()]}
        database.close()
        print(_dump(payload, args.pretty))
        return 0

    if args.command == "tax-estimate":
        database = _open_db(args.db_path)
        estimate = TaxPlanner().estimate_liability(
            database.list_transactions(),
            tax_rate=Decimal(args.rate),
        )
        database.close()
        print(_dump(estimate.as_dict(), args.pretty))
        return 0

    if args.command == "render-invoice":
        payload = json.loads(Path(args.invoice_json).read_text(encoding="utf-8"))
        path = InvoiceRenderer().write_html(Invoice.from_dict(payload), args.output_html)
        print(json.dumps({"output": str(path)}))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


def _open_db(path: str) -> HubDatabase:
    database = HubDatabase(path)
    database.init_schema()
    return database


def _dump(payload: object, pretty: bool) -> str:
    if pretty:
        return json.dumps(payload, indent=2, sort_keys=True)
    return json.dumps(payload, sort_keys=True)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
