# Integraties

FISCAi Octopus API Connector is een plugin voor Grok Bot en een standaard MCP-stdio-server. Alles wat MCP over stdio spreekt kan hem gebruiken; alles wat CSV, xlsx, JSON of Parquet leest kan zijn exports gebruiken.

| Nood | Hoe | Voorbeeld |
|---|---|---|
| AI-client (Grok Bot, Cursor, Claude Desktop/Code, VS Code, Windsurf, andere) | MCP-server registreren | [`examples/*.json`](../../examples), [agents/](../../agents/README.md) |
| Rekenblad of BI (Excel, Power BI, Google Sheets, Metabase...) | `octopus-api-connector export ... --format xlsx\|csv\|parquet` naar een map die de tool leest | [EXPORT-SCHEMA.md](../EXPORT-SCHEMA.md) |
| Geplande taken (cron, Windows Taakplanner, n8n, GitHub Actions) | `workflows run` / `sync` / `export` via de opdrachtregel | [`examples/workflows/`](../../examples/workflows) |
| Meldingen, auditlog, kopieën van exports | Hooks | [HOOKS.nl.md](../HOOKS.nl.md), [`examples/hooks/`](../../examples/hooks) |
| API verkennen | Postman-collectie (alleen lezen) | [POSTMAN.nl.md](../POSTMAN.nl.md) |

**Let op de daglimieten** in elke integratie: plan hoogstens enkele synchronisaties per dag per dossier, zet `OCTOPUS_CACHE_KEY` en een blijvende `OCTOPUS_DATA_DIR`, en laat BI-tools de geëxporteerde bestanden lezen in plaats van de connector telkens aan te roepen. Gehoste runners (bv. GitHub Actions) bewaren de cache niet tussen runs.

Formaten van andere tools veranderen; volg hun actuele documentatie (verifieer actuele documentatie). Niets hiervan vraagt een betalend plan van ons, en we maken geen accounts voor u aan.

Powered by FISCALCI Accounting & Tax (Askin Alci)

[English](README.md)
