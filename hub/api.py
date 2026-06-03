"""FastAPI app factory."""

from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path
from typing import Any

from hub.db import HubDatabase
from hub.taxes import TaxPlanner


def create_app(db_path: str | Path | None = None):
    try:
        from fastapi import FastAPI, HTTPException
    except ImportError as exc:  # pragma: no cover - optional runtime integration
        raise RuntimeError("FastAPI is not installed") from exc

    app = FastAPI(title="sannikov.dev hub", version="0.1.0")
    selected_db_path = db_path or os.environ.get("HUB_DB", "data/hub.db")
    database = HubDatabase(selected_db_path)
    database.init_schema()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/transactions")
    def transactions() -> dict[str, Any]:
        return {"transactions": [item.as_dict() for item in database.list_transactions()]}

    @app.post("/transactions")
    def add_transaction(payload: dict[str, Any]) -> dict[str, Any]:
        try:
            transaction = database.add_transaction(
                amount=payload["amount"],
                currency=payload["currency"],
                kind=payload["kind"],
                posted_on=payload.get("posted_on"),
                note=payload.get("note", ""),
                counterparty=payload.get("counterparty", ""),
                rate_to_amd=payload.get("rate_to_amd"),
            )
        except (KeyError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return transaction.as_dict()

    @app.get("/tax/estimate")
    def tax_estimate(rate: str = "0.20") -> dict[str, str]:
        estimate = TaxPlanner().estimate_liability(
            database.list_transactions(),
            tax_rate=Decimal(rate),
        )
        return estimate.as_dict()

    return app
