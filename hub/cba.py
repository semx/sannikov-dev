"""Central Bank of Armenia exchange rate helpers."""

from __future__ import annotations

import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from decimal import Decimal


CBA_ENDPOINT = "https://api.cba.am/exchangerates.asmx"


@dataclass(frozen=True, slots=True)
class ExchangeRate:
    currency: str
    rate: Decimal
    rate_date: str

    def as_dict(self) -> dict[str, str]:
        return {
            "currency": self.currency,
            "rate": str(self.rate),
            "rate_date": self.rate_date,
        }


class CBAClient:
    """Build, send, and parse exchange rate SOAP requests."""

    def __init__(self, endpoint: str = CBA_ENDPOINT, timeout: int = 10) -> None:
        self.endpoint = endpoint
        self.timeout = timeout

    def build_request(self, rate_date: date) -> bytes:
        body = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <ExchangeRatesByDate xmlns="http://www.cba.am/">
      <date>{rate_date.isoformat()}</date>
    </ExchangeRatesByDate>
  </soap:Body>
</soap:Envelope>"""
        return body.encode("utf-8")

    def fetch_rates(self, rate_date: date) -> tuple[ExchangeRate, ...]:
        request = urllib.request.Request(
            self.endpoint,
            data=self.build_request(rate_date),
            headers={
                "Content-Type": "text/xml; charset=utf-8",
                "SOAPAction": "http://www.cba.am/ExchangeRatesByDate",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = response.read()
        return self.parse_rates(payload)

    def parse_rates(self, payload: bytes | str) -> tuple[ExchangeRate, ...]:
        text = payload.decode("utf-8") if isinstance(payload, bytes) else payload
        root = ET.fromstring(text)
        rates = []

        for rate_node in root.iter():
            if _local_name(rate_node.tag).lower() not in {"exchangerate", "rate"}:
                continue

            values = {
                _local_name(child.tag).lower(): (child.text or "").strip()
                for child in list(rate_node)
            }
            currency = values.get("iso") or values.get("currency") or values.get("currencycode")
            rate = values.get("rate") or values.get("amount")
            rate_date = values.get("date") or values.get("ratedate") or ""
            if currency and rate:
                rates.append(
                    ExchangeRate(
                        currency=currency.upper(),
                        rate=Decimal(rate),
                        rate_date=rate_date,
                    )
                )

        return tuple(rates)


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag
