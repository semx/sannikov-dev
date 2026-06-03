from datetime import date
from decimal import Decimal
from unittest import TestCase

from hub.cba import CBAClient


class CBAClientTest(TestCase):
    def test_builds_exchange_rate_request(self) -> None:
        request = CBAClient().build_request(date(2026, 1, 15)).decode("utf-8")

        self.assertIn("<date>2026-01-15</date>", request)
        self.assertIn("ExchangeRatesByDate", request)

    def test_parses_exchange_rate_response(self) -> None:
        xml = """
        <Envelope>
          <Body>
            <ExchangeRatesByDateResponse>
              <ExchangeRatesByDateResult>
                <ExchangeRate>
                  <ISO>USD</ISO>
                  <Rate>405.25</Rate>
                  <Date>2026-01-15</Date>
                </ExchangeRate>
                <ExchangeRate>
                  <ISO>EUR</ISO>
                  <Rate>440.10</Rate>
                  <Date>2026-01-15</Date>
                </ExchangeRate>
              </ExchangeRatesByDateResult>
            </ExchangeRatesByDateResponse>
          </Body>
        </Envelope>
        """

        rates = CBAClient().parse_rates(xml)

        self.assertEqual(len(rates), 2)
        self.assertEqual(rates[0].currency, "USD")
        self.assertEqual(rates[0].rate, Decimal("405.25"))
