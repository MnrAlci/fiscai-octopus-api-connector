<p align="center">
  <img src="assets/logo.png" alt="FISCAi Octopus API Connector, plugin for Grok Bot" width="220">
</p>

<h1 align="center">FISCAi Octopus API Connector <br><sub>Plugin for Grok Bot, also works in Copilot, Claude, Cursor, Windsurf and other MCP clients</sub></h1>

<p align="center"><b>Read-only access to the Octopus accounting REST API, built around its very low daily limits: cache first, sync through the modified-since endpoints, never a paid plan.</b></p>

<p align="center">
  <img src="docs/images/badge-license.svg" alt="License: Apache-2.0">
  <img src="docs/images/badge-python.svg" alt="Python 3.10+">
  <img src="docs/images/badge-mcp.svg" alt="MCP over stdio, local">
  <img src="docs/images/badge-readonly.svg" alt="Read-only by default">
  <img src="docs/images/badge-limits.svg" alt="Daily limits enforced before each call">
</p>

<p align="center"><a href="README.nl.md">Nederlands</a> &middot; <a href="docs/TOOLS.md">Tools</a> &middot; <a href="docs/manuals/manual.en.md">Manual</a> &middot; <a href="CHANGELOG.md">Changelog</a></p>

Powered by FISCALCI Accounting & Tax (Askin Alci)

Author: Askin Alci

> **Belgium.** Made for Belgian accountants and bookkeepers: it follows the Belgian chart of accounts (MAR) and Belgian VAT. Outside Belgium, check the local rules yourself.

**Nederlandse samenvatting.** Bedoeld voor Belgische boekhouders/accountants; gebaseerd op Belgische boekhoud- en btw-regels (MAR, Belgisch btw-stelsel). Gebruik buiten België: verifieer zelf de lokale regels. Zie [README.nl.md](README.nl.md).

## About

FISCAi Octopus API Connector is a local MCP server (stdio) and command-line tool that lets Grok Bot and other MCP clients read Octopus dossiers: fiscal years, journals, chart of accounts, balances per period, booking lines, customers and suppliers, open items and reports. On top of that it builds what the API does not offer directly (a **trial balance**, ageing, MAR key figures) and produces exports and a **dossier transfer package per fiscal year** for the next accountant. Status: **1.0.0**, tested offline against a mocked API built from the official specification; not yet validated against a live Octopus dossier (see [open questions](docs/OPEN-QUESTIONS.md)).

## Contents

[What it does](#what-it-does) · [Daily limits](#daily-limits-and-how-the-connector-copes) · [Install](#install) · [Configuration](#configuration) · [Security](#security-and-safety) · [Tools](#tools) · [Limitations](#limitations) · [License](#license)

**More.** [Setup](docs/SETUP.md) · [Manual (EN)](docs/manuals/manual.en.md) · [Handleiding (NL)](docs/manuals/handleiding.nl.md) · [CLI](docs/CLI.md) · [Hooks](docs/HOOKS.md) · [Automation](docs/AUTOMATION.md) · [Dossier transfer](docs/DOSSIER-TRANSFER.md) · [Export schema](docs/EXPORT-SCHEMA.md) · [Integrations](docs/integrations/README.md) · [Postman](docs/POSTMAN.md) · [Write mode](docs/WRITE.md) · [Operations](docs/OPERATIONS.md) · [Privacy and data flow](docs/PRIVACY-DATA-FLOW.md) · [Troubleshooting](docs/TROUBLESHOOTING.md) · [Open questions](docs/OPEN-QUESTIONS.md) · [Agents](AGENTS.md)

## What it does

- **49 read-only tools** (51 with the optional write mode): dossiers, fiscal years, journals, chart of accounts, balances, booking lines, relations, open items, history reports, invoices, delivery notes, reminders, master data.
- **Trial balance** built from accounts and balances per period, because Octopus has no trial-balance endpoint; with a balance check and totals per MAR class.
- **Analyses:** ageing of open items, MAR key figures (revenue, costs, result, cash, receivables, payables, VAT indication), comparison with the previous fiscal year.
- **Local sync** through the official modified-since endpoints: one full load, then only changes. Encrypted on disk with your own key, or memory only.
- **Export** to CSV, JSON, Excel (xlsx) and Parquet for Power BI, Excel, databases and notebooks.
- **Dossier transfer per fiscal year**: chart of accounts, closing trial balance, booking lines, open items at year end, journals, relations, VAT codes, `CONTROL.md` checks and `MANIFEST.json` with SHA-256, resumable when a daily limit is hit.
- **Automation:** meeting preparation and recurring obligations (VAT, listings, annual accounts) as overviews and draft e-mails; nothing is sent by default.
- **Free official helpers (optional):** Belgian VAT-number check (offline modulo 97, optional VIES of the European Commission) and ECB euro reference rates.

## Daily limits and how the connector copes

The official Octopus REST specification sets a **maximum number of calls per day per endpoint**. Some are very low:

| Endpoint group | Calls per day |
|---|---|
| Accounts, VAT codes, currencies, cost centres, custom fields, products, product groups; relations without search | **2** |
| One purchase/sales or financial/miscellaneous booking | 10 |
| Fiscal years, journals, reports (open items, history) | 24 |
| All *modified-since* endpoints | 48 |
| Dossier list and dossier token | 150 |
| Relations with a search term, invoices, delivery notes, reminders | 400 |

So the connector:

1. **counts every call before sending it** and refuses when today's limit (Europe/Brussels) is reached, instead of letting Octopus send you a warning e-mail (`octopus_quota` shows what is left);
2. **caches** responses according to the limit (12 hours for 2/day master data);
3. **syncs** accounts, balances, relations and bookings with the modified-since endpoints (first load per fiscal year and journal type with `1980-01-01 00:00:00.000`, then fiscal year `-1` and journal type `-1` with the last watermark), exactly as the specification describes;
4. **refreshes the 10-minute tokens** (authentication token and dossier token) automatically, one minute before they expire, and retries once on HTTP 401;
5. never uses the paid **Management API**, the file-import API or any paid plan.

## Install

Requirements: Python 3.10+, `httpx`, `cryptography` (and `pyarrow` only for Parquet). Octopus API access: a **software house UUID** from Octopus and an Octopus user with API rights. There is **no sandbox**; use the demo dossier for testing (verifieer actuele regel).

**Grok Bot.** Add the plugin from its repository and fill in the variables `OCTOPUS_SOFTWARE_HOUSE_UUID`, `OCTOPUS_USER` and `OCTOPUS_PASSWORD` (secrets). Then ask, for example: *"Show the trial balance of dossier 101 for 2026"* (example dossier number).

**Command line.**

```bash
pip install -r requirements.txt
python server/run_cli.py config init          # writes a .env with placeholders only
python server/run_cli.py doctor               # checks Python, dependencies and configuration; makes no call
python server/run_cli.py call octopus_dossiers
python server/run_cli.py sync --dossier 101 --bookyear 2
python server/run_cli.py call octopus_proefbalans dossier_id=101 jaar=2026
python server/run_cli.py transfer --dossier 101 --out ./overdracht          # estimate first; add --yes to run
```

**Other MCP clients** (Cursor, Claude Desktop/Code, VS Code Copilot, Windsurf): see [examples/](examples/) for ready-made configuration files; they all start `server/run_server.py` over stdio.

## Configuration

| Variable | Meaning |
|---|---|
| `OCTOPUS_SOFTWARE_HOUSE_UUID` | Software house UUID (header `softwareHouseUuid`). Secret. |
| `OCTOPUS_USER`, `OCTOPUS_PASSWORD` | Octopus user with API access. Secret; memory only, never logged. |
| `OCTOPUS_CACHE_KEY` | Optional, 16+ characters: encrypts cache and sync on disk. Without it everything stays in memory. |
| `OCTOPUS_LOCALE_ID` | `localeId` for the dossier token (0-4, default 1; verifieer actuele regel). |
| `OCTOPUS_ALLOWED_DOSSIERS` | Optional comma-separated allow-list of dossier ids. |
| `OCTOPUS_QUOTA_RESERVE` | Calls per endpoint kept in reserve (default 0). |
| `OCTOPUS_AMOUNTS_MODE` | `movement` (default) or `cumulative`: how balances per period are read (verifieer actuele regel). |
| `OCTOPUS_WRITE_ENABLED` | Off by default. `true` adds the two-step write tools. |
| `OCTOPUS_DATA_DIR`, `OCTOPUS_HOOKS_FILE`, `OCTOPUS_LOG_LEVEL` | Data folder, hooks file, log level. |

## Security and safety

- **Read-only by default.** Write tools do not exist unless `OCTOPUS_WRITE_ENABLED=true`; even then every write is a proposal first and needs a confirmation code, with a daily maximum. Delete operations are never offered. See [WRITE.md](docs/WRITE.md).
- **Your credentials, your computer.** No central server. Tokens live in memory only; secrets are scrubbed from every output, log and error.
- **Only the official host.** The base URL must be `https://service.inaras.be/octopus-rest-api/...`; the Management API is refused.
- **No client data in this repository.** Examples use `[Voorbeeld]` data only.
- No tax or legal advice: check figures against the source and the current rules.

## Tools

See [docs/TOOLS.md](docs/TOOLS.md) for all tools with their Octopus endpoint and daily limit (generated from the code).

## Limitations

- Not yet validated against a live Octopus dossier; several API details are marked **verifieer actuele regel** and listed in [docs/OPEN-QUESTIONS.md](docs/OPEN-QUESTIONS.md) (for example whether balances per period are movements or cumulative, and the exact error object).
- No pagination in the API: large lists come in one response; tools cap what they show (`max_rijen`), exports always contain everything.
- Attachments (file sync), OAuth and a dashboard widget are on the [roadmap](ROADMAP.md).

## Shared core

The reusable parts (MCP server, CLI base, hooks, export layer, automation, dossier-transfer package, token cache, daily-limit counter, encrypted store, trial-balance builder, analyses) live in **FISCAi Accounting API Core** and are vendored in `server/vendor/accounting_api_core` (`python scripts/sync_core.py`).

## License

Apache License 2.0, see [LICENSE](LICENSE) and [NOTICE](NOTICE). The attribution "Powered by FISCALCI Accounting & Tax (Askin Alci)" must stay intact in every copy and in generated exports.

Octopus is a trademark of its owner; this project is not endorsed by it.

Powered by FISCALCI Accounting & Tax (Askin Alci)
