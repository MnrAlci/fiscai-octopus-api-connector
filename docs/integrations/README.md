# Integrations

FISCAi Octopus API Connector is a plugin for Grok Bot and a standard MCP stdio server. Anything that speaks MCP over stdio can use it; anything that reads CSV, xlsx, JSON or Parquet can use its exports.

| Need | How | Example |
|---|---|---|
| AI client (Grok Bot, Cursor, Claude Desktop/Code, VS Code, Windsurf, others) | Register the MCP server | [`examples/*.json`](../../examples), [agents/](../../agents/README.md) |
| Spreadsheet or BI (Excel, Power BI, Google Sheets, Metabase...) | `octopus-api-connector export ... --format xlsx\|csv\|parquet` into a folder the tool reads | [EXPORT-SCHEMA.md](../EXPORT-SCHEMA.md) |
| Scheduled jobs (cron, Windows Task Scheduler, n8n, GitHub Actions) | `workflows run` / `sync` / `export` from the CLI | [`examples/workflows/`](../../examples/workflows) |
| Notifications, audit log, copies of exports | Hooks | [HOOKS.md](../HOOKS.md), [`examples/hooks/`](../../examples/hooks) |
| API exploration | Postman collection (read-only) | [POSTMAN.md](../POSTMAN.md) |

**Mind the daily limits** in every integration: schedule at most a few syncs per day per dossier, set `OCTOPUS_CACHE_KEY` and a persistent `OCTOPUS_DATA_DIR`, and let BI tools read the exported files instead of calling the connector repeatedly. Hosted runners (for example GitHub Actions) do not keep the cache between runs.

Formats of third-party tools change; follow their current docs (verify current docs). Nothing here needs a paid plan from us, and we register no accounts for you.

Powered by FISCALCI Accounting & Tax (Askin Alci)

[Nederlands](README.nl.md)
