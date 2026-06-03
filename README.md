# sannikov.dev

[![tests](https://github.com/semx/sannikov-dev/actions/workflows/tests.yml/badge.svg)](https://github.com/semx/sannikov-dev/actions/workflows/tests.yml)

Personal tech hub and self-hosted financial automation toolkit for contractor
work.

The project combines a small API surface, SQLite-backed bookkeeping, exchange
rate lookup helpers, invoice rendering, and reminder logic for quarterly tax
planning. The core modules are dependency-light so they can be tested locally;
FastAPI and WeasyPrint integrations are available when installed in the runtime
environment.

## Features

- Track incoming contractor payments and operating expenses in SQLite.
- Normalize amounts across currencies with Central Bank of Armenia exchange
  rate payloads.
- Generate invoice HTML and optional PDF output.
- Calculate quarterly tax reminders and simple projected liabilities.
- Send Telegram notifications through a small API client.
- Expose a FastAPI app factory for self-hosted deployment.

## Quick start

```bash
python3 -m unittest discover -s tests
python3 -m hub.cli init-db data/hub.db
python3 -m hub.cli add-transaction data/hub.db --amount 2500 --currency USD --kind income --note "contract invoice"
python3 -m hub.cli transactions data/hub.db --pretty
```

## Runtime integrations

The repository keeps external integrations behind narrow boundaries:

- `hub.cba` builds and parses exchange rate SOAP payloads.
- `hub.telegram` sends bot notifications with `urllib`.
- `hub.api` creates a FastAPI app when FastAPI is available.
- `hub.invoices` renders HTML and can call WeasyPrint for PDF generation.

This makes the accounting logic easy to verify without network access.
