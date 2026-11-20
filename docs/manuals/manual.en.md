# FISCAi Octopus API Connector: complete manual

> Intended for Belgian bookkeepers/accountants; based on Belgian accounting and VAT rules (MAR, Belgian VAT system). Use outside Belgium: verify the local rules yourself.
>
> Powered by FISCALCI Accounting & Tax (Askin Alci)

This manual explains every feature step by step. The connector is a plugin for Grok Bot (it also works in Copilot, Claude, Cursor, Windsurf and other MCP clients) and a command-line tool that reads your Octopus accounting data locally with your own Octopus user. It is **read-only by default**, uses only the free Octopus REST API (`https://service.inaras.be/octopus-rest-api/v1`) and is not an official Octopus product. Never the Management API, never a paid plan.

## 1. What you need
1. Python 3.10 or higher.
2. An Octopus user with access to the web-service module, and a **Software House ID** (UUID) requested from Octopus.
3. There is no sandbox: test first on the Octopus **demo dossier**.

## 2. Install and first run
1. Get the code and install it: `git clone <repository-url> fiscai-octopus-api-connector`, `cd fiscai-octopus-api-connector`, `python3 -m venv .venv`, `.venv/bin/pip install .`
2. `octopus-api-connector config init` writes an example `.env` with placeholders only. Fill `OCTOPUS_SOFTWARE_HOUSE_UUID`, `OCTOPUS_USER` and `OCTOPUS_PASSWORD` in your environment or your client's secret settings; never in a chat or the repository.
3. Set `OCTOPUS_CACHE_KEY` (at least 16 characters). It enables the encrypted cache and sync on disk; without it every restart costs calls again.
4. `octopus-api-connector doctor` checks Python, packages, configuration and write mode. It makes no call and prints no secrets.
5. In Grok Bot or another MCP client, ask: "Run `octopus_status`". This makes no Octopus call.

## 3. Daily limits: the most important rule
Octopus limits calls **per endpoint per day**. Some endpoints allow only **2 calls a day** (accounts, VAT codes, currencies, cost centres, custom fields, products, product groups, relations without search), buy/sell and financial/diverse bookings 10, bookyears/journals/reports 24, the modified endpoints 48, dossiers 150, invoices and relations with search 400.

1. The connector counts every call in a local file (no dossier ids) and **refuses before sending** when a limit would be exceeded. It shows the reset time.
2. Check `octopus_quota` (or `octopus-api-connector quota`) before heavy work.
3. Use `octopus_sync` once, then work with the local tools. `vers: true` forces a new call: only when needed.
4. Calls you make elsewhere (Postman, other software) are not counted; keep a reserve with `OCTOPUS_QUOTA_RESERVE`.
5. Tokens are valid 10 minutes and are renewed automatically. Octopus has no pagination: lists come complete and tool output is capped with `max_rijen`.

## 4. Use it from an assistant
1. **Grok Bot**: install the plugin and ask in plain language: "Give me the trial balance of dossier [Voorbeeld] for 2026 up to period 6."
2. **Other MCP clients**: copy a file from `examples/` (Cursor, Claude Desktop, Claude Code, VS Code, Windsurf, generic stdio) and use the client's secret handling.
3. **Agents**: ready-made definitions are in `agents/` (section 12).

## 5. The tools, grouped by domain
There are 51 tools (`octopus_*`): 49 read-only or local tools, and 2 write tools that only exist when write mode is enabled (section 13).

### Status and daily limits (no Octopus call)

| Tool | What it does | Octopus endpoint (daily limit) |
|---|---|---|
| `octopus_status` | Configuration (without secrets), daily limits, cache and version. Makes no Octopus call. | local |
| `octopus_quota` | Used and remaining calls per Octopus endpoint today (Europe/Brussels). Makes no call. | local |
| `octopus_sync_status` | Watermarks and record counts of the local sync. Makes no call. | local |
| `octopus_export_schema` | Columns and types of the export datasets (Power BI, Excel, databases). Makes no call. | local |

### Session, dossiers and fiscal years

| Tool | What it does | Octopus endpoint (daily limit) |
|---|---|---|
| `octopus_api_versie` | Version of the Octopus REST API. | `GET /about/version` |
| `octopus_whoami` | Information about the signed-in Octopus user. | `GET /authentication` |
| `octopus_dossiers` | Dossiers the user can access (respects OCTOPUS_ALLOWED_DOSSIERS). | `GET /dossiers` (150/day) |
| `octopus_boekjaren` | Fiscal years with their periods. | `GET /dossiers/{dossierId}/bookyears` (24/day) |
| `octopus_boekjaar_detail` | Details of one fiscal year. | `GET /dossiers/{dossierId}/bookyears/{bookyearId}` (24/day) |
| `octopus_boekjaar_status` | Fiscal year status: closed or open, journals, protected/closed periods and sync state. | `GET /dossiers/{dossierId}/bookyears` (24/day)<br>`GET /dossiers/{dossierId}/bookyears/{bookyearId}/journals` (24/day) |
| `octopus_dagboeken` | Journals of a fiscal year. | `GET /dossiers/{dossierId}/bookyears/{bookyearId}/journals` (24/day) |
| `octopus_dagboek_detail` | Detail of one journal by type (A/V/F/D/L). | `GET /dossiers/{dossierId}/bookyears/{bookyearId}/journals/A/{sequenceNumber}` (24/day) |
| `octopus_dagboeksaldo` | Balance of a (financial) journal. | `GET /dossiers/{dossierId}/bookyears/{bookyearId}/journals/{journalKey}` (24/day) |
| `octopus_dagboeken_gewijzigd` | Journals modified since a timestamp. | `GET /dossiers/{dossierId}/journals/modified` (48/day) |

### Ledger via local sync (cache-first)

| Tool | What it does | Octopus endpoint (daily limit) |
|---|---|---|
| `octopus_sync` | Fetches accounts, balances, relations and bookings and keeps them locally via the modified-since endpoints (full load once, then changes only). | local |
| `octopus_rekeningschema` | Chart of accounts of a fiscal year, from the local sync. | `GET /dossiers/{dossierId}/accounts` (2/day)<br>`GET /dossiers/{dossierId}/accounts/modified` (48/day) |
| `octopus_rekeningsaldi` | Balances per account per period, from the local sync. | `GET /dossiers/{dossierId}/accounts/amounts/modified` (48/day) |
| `octopus_proefbalans` | Trial balance built from accounts and balances per period (Octopus has no trial-balance endpoint); balance check and totals per MAR class. | local |
| `octopus_boekingslijnen` | Booking lines of a fiscal year, from the local sync (first time 4 calls per year, then 1). | `GET /dossiers/{dossierId}/bookyears/{bookyearId}/bookings/modified` (48/day) |
| `octopus_relaties` | Customers and suppliers; without a search term from the sync, with a search term directly (400/day). | `GET /dossiers/{dossierId}/relations` (2/day)<br>`GET /dossiers/{dossierId}/relations/modified` (48/day)<br>`GET /dossiers/{dossierId}/relations` (400/day) |

### Reports, open items and analyses

| Tool | What it does | Octopus endpoint (daily limit) |
|---|---|---|
| `octopus_openstaande_posten` | Open items of customers (receivables), suppliers (payables) or one account. | `POST /dossiers/{dossierId}/reports/clients/open` (24/day) |
| `octopus_ouderdom_openstaande_posten` | Ageing of open items (not due, 0-30, 31-60, 61-90, over 90 days, no date, negative). | `POST /dossiers/{dossierId}/reports/clients/open` (24/day) |
| `octopus_historiek` | History report per account, customer, supplier or cost centre over a fiscal-year and period range. | `POST /dossiers/{dossierId}/reports/accounts/history` (24/day) |
| `octopus_dashboard_kpis` | Key figures from the built trial balance (revenue, costs, result, cash, VAT indication) plus open receivables/payables (Belgian MAR). | local |

### Bookings and documents (read)

| Tool | What it does | Octopus endpoint (daily limit) |
|---|---|---|
| `octopus_boekingen_gewijzigd` | Raw sync call: booking lines modified since a timestamp. Prefer octopus_sync. | `GET /dossiers/{dossierId}/bookyears/{bookyearId}/bookings/modified` (48/day) |
| `octopus_aankoop_verkoop_boeking` | One purchase or sales document with its lines (10/day). | `GET /dossiers/{dossierId}/buysellbookings` (10/day) |
| `octopus_aankoop_verkoop_gewijzigd` | Purchase/sales documents modified since a timestamp. | `GET /dossiers/{dossierId}/buysellbookings/modified` (48/day) |
| `octopus_financieel_divers_boeking` | One financial or miscellaneous document with its lines (10/day). | `GET /dossiers/{dossierId}/financialdiversbookings` (10/day) |
| `octopus_financieel_divers_gewijzigd` | Financial/miscellaneous documents modified since a timestamp. | `GET /dossiers/{dossierId}/financialdiversbookings/modified` (48/day) |
| `octopus_onafgepunte_facturen` | Invoices that are not yet matched (balanced). | `GET /dossiers/{dossierId}/bank/invoices` (48/day) |
| `octopus_afpuntingen_gewijzigd` | Matchings (balancings) modified since a timestamp. | `GET /dossiers/{dossierId}/balancings/modified` (48/day) |
| `octopus_betaallijst` | Contents of the payment list (read only). | `GET /dossiers/{dossierId}/bank/paymentlist` (48/day) |
| `octopus_enveloppes` | Payment envelopes or the contents of one envelope (read only). | `GET /dossiers/{dossierId}/bank/enveloppes` (48/day) |
| `octopus_facturen_gewijzigd` | Invoices from the invoicing module modified since a timestamp (module must be active). | `GET /dossiers/{dossierId}/invoices/modified` (48/day) |
| `octopus_factuur` | One invoice from the invoicing module. | `GET /dossiers/{dossierId}/invoices` (400/day) |
| `octopus_leveringsbonnen_gewijzigd` | Delivery notes modified since a timestamp. | `GET /dossiers/{dossierId}/deliverynotes/modified` (48/day) |
| `octopus_rappels` | Reminder (dunning) information up to a due date. | `GET /dossiers/{dossierId}/rappels` (400/day) |

### Master data (2 calls per day: cached 12 h)

| Tool | What it does | Octopus endpoint (daily limit) |
|---|---|---|
| `octopus_btw_codes` | VAT codes of the dossier (master data: 2 calls per day, cached 12 h). | `GET /dossiers/{dossierId}/vatcodes` (2/day) |
| `octopus_munten` | Currency codes of the dossier (master data). | `GET /dossiers/{dossierId}/currencies` (2/day) |
| `octopus_vrije_velden` | Custom fields of the dossier (master data). | `GET /dossiers/{dossierId}/customfields` (2/day) |
| `octopus_producten` | Products (master data). | `GET /dossiers/{dossierId}/products` (2/day) |
| `octopus_productgroepen` | Product groups (master data). | `GET /dossiers/{dossierId}/productgroups` (2/day) |
| `octopus_kostenplaatsen` | Cost centres, optionally active only (master data). | `GET /dossiers/{dossierId}/costcentres` (2/day) |

### Export and dossier transfer

| Tool | What it does | Octopus endpoint (daily limit) |
|---|---|---|
| `octopus_export_dataset` | Writes a dataset (kpis, balances, trial balance, open items, booking lines, chart of accounts, relations) to CSV, JSON, Excel or Parquet. Never writes to Octopus. | local |
| `octopus_dossier_transfer_schatting` | Estimates the calls per endpoint for a per-fiscal-year transfer and compares them with the remaining daily limits. | local |
| `octopus_dossier_transfer_export` | Complete per-fiscal-year package for the next accountant, with CONTROL.md, MANIFEST.json (SHA-256) and README. Read only; resumable. | local |

### Free official helpers and error codes

| Tool | What it does | Octopus endpoint (daily limit) |
|---|---|---|
| `octopus_btw_nummer_controle` | Offline check of a Belgian VAT number (modulo 97), optionally a VIES check with the European Commission (free, no key). | local |
| `octopus_wisselkoers_ecb` | ECB euro reference rate for a currency (free, for information). | local |
| `octopus_foutcode_uitleg` | Fetches the sample error object for an Octopus error code (100/day). | `GET /error` (100/day) |

### Write (OFF by default; OCTOPUS_WRITE_ENABLED=true, two steps)

| Tool | What it does | Octopus endpoint (daily limit) |
|---|---|---|
| `octopus_schrijf_voorstel` | Step 1: prepares a write action and shows exactly what would be sent, with a confirmation code. Sends nothing. | local |
| `octopus_schrijf_bevestigen` | Step 2: sends a prepared proposal to Octopus with its confirmation code (WRITES; daily maximum). | local |


## 6. Sync, trial balance and key figures
1. `octopus_dossiers`, then `octopus_boekjaren` for the dossier.
2. `octopus_sync` (or `octopus-api-connector sync --dossier <id>`): the first time it loads everything per bookyear and journal type; afterwards only changes via the modified endpoints. Deleted bookings are removed. `octopus_sync_status` shows the watermarks.
3. `octopus_proefbalans`: Octopus has no trial-balance endpoint, so the connector **builds** it from the chart of accounts and the balances per account per period. Balance = debit minus credit (revenue is negative); it checks debit = credit and totals per MAR class.
4. Whether period balances are movements or cumulative (`OCTOPUS_AMOUNTS_MODE`) and the sign convention must be verified on the demo dossier: verifieer actuele regel.
5. `octopus_openstaande_posten` and `octopus_ouderdom_openstaande_posten` (customers or suppliers, reference date). A negative open amount is an item to check, not a conclusion.
6. `octopus_dashboard_kpis`: revenue, costs, result, margin, liquid assets, open items, DSO/DPO, for a year, a month (`maand:5`) or a quarter (`kwartaal:2`).

## 7. Export layer (CSV, JSON, xlsx, Parquet)
1. `octopus-api-connector export proefbalans --dossier <id> --out ./export --format csv --format xlsx` or the tool `octopus_export_dataset`.
2. Datasets: `kpis`, `saldi`, `proefbalans`, `openstaande_posten` (with `--kind debiteuren|crediteuren`), `boekingslijnen`, `rekeningschema`, `relaties`. Fixed schema: `docs/EXPORT-SCHEMA.md`. Parquet needs the optional `pyarrow`.
3. Let Excel, Power BI or other tools read the files instead of calling the connector repeatedly.

## 8. Command line
| Command | Purpose |
|---|---|
| `serve` | start the MCP server (stdio) |
| `doctor` | check the environment (no calls) |
| `tools`, `call TOOL name=value` | list tools; call one read-only tool |
| `sync`, `quota`, `cache status|clear` | sync, daily limits, local cache |
| `export`, `transfer` | exports and dossier transfer |
| `workflows init|list|plan|run` | automation |
| `config init`, `version`, `completion` | configuration, version, shell completion |

Common options: `--json`, `--quiet`, `--verbose`, `--log-level`, `--log-format json`, `--env-file`, `--hooks`, `--dry-run`, `--data-dir`. Exit codes: 0 ok, 1 error, 2 usage, 3 configuration, 4 tool/Octopus error, 5 network, 6 refused (daily limit, write tool, dossier not allowed). Details: `docs/CLI.md`.

## 9. Hooks (optional, off by default)
1. Copy `examples/hooks/hooks.example.toml` and set `enabled = true`.
2. Events: `pre_call`, `post_call`, `on_error`, `on_export`, each with a local command (list, no shell) or a Python function.
3. Start with `--hooks FILE` or `OCTOPUS_HOOKS_FILE`. Hooks never receive secrets and never break a call. Details: `docs/HOOKS.md`.

## 10. Automation
1. `octopus-api-connector workflows init --path workflows.toml` writes an example with `[Voorbeeld]` data; each client needs `dossier_id`.
2. `workflows plan` shows what is due (no Octopus calls); `workflows run` writes overviews per meeting and per due obligation, and **draft** e-mails (`.eml`).
3. Deadlines in the example are examples marked "verifieer actuele regel". Mails are never sent by default.
4. Schedule with cron, Windows Task Scheduler, n8n or GitHub Actions (`examples/workflows/`); keep the cache on a persistent machine to save the daily limits. Details: `docs/AUTOMATION.md`.

## 11. Dossier transfer per fiscal year
1. Estimate: `octopus-api-connector transfer --dossier <id> --out ./overdracht` (without `--yes`) shows the calls per endpoint against today's limits.
2. Run with `--yes` (optionally `--bookyear` per year, `--no-lines`, `--zip`). Master data may be fetched only twice a day, so a multi-year transfer can take more than one day: repeat the command later and it resumes from the checkpoint.
3. Read `CONTROL.md`, `MANIFEST.json` (SHA-256) and the `README.md` for the receiving bookkeeper.
4. Hand over securely and observe the professional, GDPR and retention points (verifieer actuele regel). Details: `docs/DOSSIER-TRANSFER.md`.

## 12. Agents, Postman and integrations
- **Agents**: `agents/README.md` lists Grok Bot, Claude Code, Claude Desktop, GitHub Copilot, Cursor and a generic system prompt. Nothing is installed for you.
- **Postman**: import the collection and environment from `postman/`; it contains only the 50 read operations. Every request counts towards the daily limits and is not counted by the connector (`docs/POSTMAN.md`).
- **Integrations**: `docs/integrations/README.md`.

## 13. Write mode (off by default)
Only with `OCTOPUS_WRITE_ENABLED=true`. Two steps: `octopus_schrijf_voorstel` shows exactly what would be sent and returns a code valid 10 minutes; `octopus_schrijf_bevestigen` sends it. Only six actions are possible (update relation, create/update buy-sell booking, create/update financial-diverse booking, add balancing); never delete. Maximum `OCTOPUS_WRITE_MAX_PER_DAY` (default 20). The command line always refuses write tools. Read `docs/WRITE.md` first; most users never enable it.

## 14. Free helpers
`octopus_btw_nummer_controle` checks a VAT number with the Belgian check digit and optionally VIES; `octopus_wisselkoers_ecb` gives ECB reference rates. Both are free public services and only called when you use them.

## 15. Privacy, open questions and help
- Data stays on your computer; what the assistant sees goes to the model provider you chose (`docs/PRIVACY-DATA-FLOW.md`).
- Points not yet confirmed (amounts mode, sign, limits counting, error format) are listed in `docs/OPEN-QUESTIONS.md`: verifieer actuele regel.
- Not tax or legal advice: have figures reviewed by your bookkeeper/accountant.
- Problems: `docs/TROUBLESHOOTING.md`; run `octopus-api-connector doctor`.

Powered by FISCALCI Accounting & Tax (Askin Alci)
