# Command line: `octopus-api-connector`

> Intended for Belgian bookkeepers/accountants; based on Belgian accounting and VAT rules (MAR, Belgian VAT system). Use outside Belgium: verify the local rules yourself.
>
> Powered by FISCALCI Accounting & Tax (Askin Alci)

Installed as `octopus-api-connector` (`pip install .`), or run without installing: `python3 server/run_cli.py ...`. Dutch: [CLI.nl.md](CLI.nl.md).

## Commands

| Command | What it does | Octopus calls |
|---|---|---|
| `serve` | Starts the MCP server over stdio (same as `server/run_server.py`). | per tool |
| `doctor` | Checks Python, dependencies, configuration, encrypted cache, write mode and attribution. Never prints secrets. | none |
| `tools [--json]` | Lists all tools (49 read-only; 2 more with write mode). | none |
| `call TOOL name=value ...` | Runs one **read-only** tool. Values may be JSON (`jaren=[2025,2026]`). Write tools are refused (exit 6). | per tool |
| `sync --dossier ID [--bookyear ID]` | Syncs accounts, balances, relations and bookings (first full load, then changes only). | 4-8 first time, then 4 |
| `quota [--json]` | Used and remaining calls per endpoint today. | none |
| `export DATASET --dossier ID --out DIR [--bookyear ID] [--kind debiteuren\|crediteuren] [--format csv ...]` | Writes `kpis`, `saldi`, `proefbalans`, `openstaande_posten`, `boekingslijnen`, `rekeningschema` or `relaties`. | from cache/sync |
| `transfer --dossier ID --out DIR [--bookyear ID ...] [--format ...] [--no-lines] [--zip] [--yes]` | Dossier transfer per fiscal year. Without `--yes` it only shows the estimate per endpoint. Resumable. | see estimate |
| `workflows init\|list\|plan\|run` | Automation: meeting preparation and recurring obligations ([AUTOMATION.md](AUTOMATION.md)). | `plan`: none |
| `cache status` / `cache clear --yes` | Shows or clears the local cache and sync (not the daily counter). | none |
| `config init [--path .env] [--force]` | Writes an example `.env` with placeholders only. | none |
| `version`, `completion bash\|zsh\|powershell` | Version; shell completion script. | none |

## Common options

`--json` (machine-readable output), `-q/--quiet`, `-v/--verbose`, `--log-level`, `--log-format text|json` (structured logs on stderr), `--env-file FILE` (the environment wins), `--hooks FILE` ([HOOKS.md](HOOKS.md)), `--dry-run` (shows what would happen, no Octopus calls), `--data-dir DIR`.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | OK |
| 1 | Error |
| 2 | Usage error (unknown tool, missing or unknown argument) |
| 3 | Configuration error (missing credentials, wrong base URL) |
| 4 | Tool or Octopus API error (error object shown, scrubbed) |
| 5 | Network error |
| 6 | Refused (daily limit reached, write tool on the command line, dossier not allowed, sending without permission) |

## Examples

```bash
octopus-api-connector doctor
octopus-api-connector call octopus_dossiers
octopus-api-connector call octopus_boekjaren dossier_id=101
octopus-api-connector sync --dossier 101 --bookyear 2
octopus-api-connector call octopus_proefbalans dossier_id=101 jaar=2026 tot_periode=6
octopus-api-connector call octopus_ouderdom_openstaande_posten dossier_id=101 soort=debiteuren
octopus-api-connector export proefbalans --dossier 101 --out ./export --format csv --format xlsx
octopus-api-connector transfer --dossier 101 --out ./overdracht            # estimate only
octopus-api-connector transfer --dossier 101 --out ./overdracht --yes --zip
octopus-api-connector quota
```

Dossier 101 and the figures are `[Voorbeeld]` values.
