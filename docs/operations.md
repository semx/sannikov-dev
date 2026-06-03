# Operations

## Backups

The service stores state in a single SQLite database. For a small self-hosted
deployment, a daily file-level backup is enough:

```bash
sqlite3 data/hub.db ".backup 'backups/hub-$(date +%Y%m%d).db'"
```

## Invoice output

HTML invoice rendering has no external dependencies:

```bash
python -m hub.cli render-invoice examples/invoice.json invoices/SS-2026-001.html
```

PDF output uses WeasyPrint through `InvoiceRenderer.write_pdf`.

## Deployment

```bash
docker compose up -d --build
curl http://localhost:8000/health
```

Keep bot tokens and deployment credentials outside the repository.
