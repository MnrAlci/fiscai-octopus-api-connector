# Roadmap

Nothing here is promised; items move when Askin decides.

## Next
- **Validation on the Octopus demo dossier** (no sandbox exists): confirm the open questions in [docs/OPEN-QUESTIONS.md](docs/OPEN-QUESTIONS.md), especially the balances mode (movement or cumulative), the sign of open amounts and the error-object variant per endpoint.
- **Attachments (file sync):** read-only listing of attachments of a booking through the REST attachment endpoints, never the separate file-import API.
- **OAuth:** support the OAuth token flow once it is clear how the token is passed to the REST API (bundle point T6).
- **Dashboard widget:** an MCP app widget with the key figures, like the Yuki connector, built on the shared core.

## Later
- Portfolio key figures across several dossiers, with a strict per-day budget so the 24/day report limits are not exhausted.
- More analyses from the synced booking lines (DSO/DPO, outliers), without extra Octopus calls.
- Optional SQLite store for very large dossiers.

## Not planned
- The paid Management API or any paid plan.
- Deleting data in Octopus, closing fiscal years, importing CODA/SODA, sending invoices.
