from decimal import Decimal
from unittest import TestCase

from hub.invoices import Invoice, InvoiceLine, InvoiceRenderer


class InvoiceRendererTest(TestCase):
    def test_calculates_total(self) -> None:
        invoice = Invoice(
            number="SS-1",
            issued_on="2026-01-01",
            due_on="2026-01-15",
            seller="Sergey Sannikov",
            client="Client",
            currency="USD",
            lines=(
                InvoiceLine("Consulting", Decimal("2"), Decimal("100.00")),
                InvoiceLine("Support", Decimal("1"), Decimal("50.00")),
            ),
        )

        self.assertEqual(invoice.total, Decimal("250.00"))

    def test_renders_html_with_escaped_values(self) -> None:
        invoice = Invoice.from_dict(
            {
                "number": "SS-2",
                "issued_on": "2026-01-01",
                "due_on": "2026-01-15",
                "seller": "Sergey Sannikov",
                "client": "Client <LLC>",
                "currency": "USD",
                "lines": [{"description": "Work <audit>", "quantity": 1, "unit_price": 120}],
            }
        )

        html = InvoiceRenderer().render_html(invoice)

        self.assertIn("Client &lt;LLC&gt;", html)
        self.assertIn("Work &lt;audit&gt;", html)
        self.assertIn("120.00 USD", html)
