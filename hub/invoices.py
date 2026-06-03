"""Invoice rendering helpers."""

from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class InvoiceLine:
    description: str
    quantity: Decimal
    unit_price: Decimal

    @property
    def total(self) -> Decimal:
        return (self.quantity * self.unit_price).quantize(Decimal("0.01"))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "InvoiceLine":
        return cls(
            description=payload["description"],
            quantity=Decimal(str(payload.get("quantity", "1"))),
            unit_price=Decimal(str(payload["unit_price"])),
        )


@dataclass(frozen=True, slots=True)
class Invoice:
    number: str
    issued_on: str
    due_on: str
    seller: str
    client: str
    currency: str
    lines: tuple[InvoiceLine, ...]
    notes: str = ""

    @property
    def total(self) -> Decimal:
        return sum((line.total for line in self.lines), Decimal("0")).quantize(Decimal("0.01"))

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Invoice":
        issued_on = payload.get("issued_on", date.today().isoformat())
        return cls(
            number=payload["number"],
            issued_on=issued_on,
            due_on=payload.get("due_on", issued_on),
            seller=payload["seller"],
            client=payload["client"],
            currency=payload.get("currency", "USD").upper(),
            lines=tuple(InvoiceLine.from_dict(line) for line in payload.get("lines", [])),
            notes=payload.get("notes", ""),
        )


class InvoiceRenderer:
    """Render invoices as HTML or PDF."""

    def render_html(self, invoice: Invoice) -> str:
        rows = "\n".join(
            "<tr>"
            f"<td>{html.escape(line.description)}</td>"
            f"<td class=\"number\">{line.quantity}</td>"
            f"<td class=\"number\">{line.unit_price}</td>"
            f"<td class=\"number\">{line.total}</td>"
            "</tr>"
            for line in invoice.lines
        )
        notes = f"<p>{html.escape(invoice.notes)}</p>" if invoice.notes else ""
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Invoice {html.escape(invoice.number)}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; color: #1f2933; }}
    main {{ max-width: 760px; margin: 40px auto; }}
    header {{ display: flex; justify-content: space-between; border-bottom: 1px solid #d8dee4; padding-bottom: 20px; }}
    h1 {{ margin: 0; font-size: 28px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 28px; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; padding: 10px; text-align: left; }}
    .number {{ text-align: right; }}
    .total {{ margin-top: 20px; text-align: right; font-size: 20px; font-weight: 700; }}
  </style>
</head>
<body>
  <main>
    <header>
      <section>
        <h1>Invoice {html.escape(invoice.number)}</h1>
        <p>Issued {html.escape(invoice.issued_on)} · Due {html.escape(invoice.due_on)}</p>
      </section>
      <section>
        <strong>{html.escape(invoice.seller)}</strong><br>
        Bill to: {html.escape(invoice.client)}
      </section>
    </header>
    <table>
      <thead>
        <tr><th>Description</th><th class="number">Qty</th><th class="number">Unit</th><th class="number">Total</th></tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>
    <div class="total">Total: {invoice.total} {html.escape(invoice.currency)}</div>
    {notes}
  </main>
</body>
</html>"""

    def write_pdf(self, invoice: Invoice, output_path: str | Path) -> Path:
        try:
            from weasyprint import HTML
        except ImportError as exc:  # pragma: no cover - optional integration
            raise RuntimeError("WeasyPrint is not installed") from exc

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        HTML(string=self.render_html(invoice)).write_pdf(path)
        return path

    def write_html(self, invoice: Invoice, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render_html(invoice), encoding="utf-8")
        return path
