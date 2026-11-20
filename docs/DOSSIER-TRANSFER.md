# Dossier transfer per fiscal year

> Intended for Belgian bookkeepers/accountants; based on Belgian accounting and VAT rules (MAR, Belgian VAT system). Use outside Belgium: verify the local rules yourself.
>
> Powered by FISCALCI Accounting & Tax (Askin Alci)

When a client moves to another bookkeeper, `octopus_dossier_transfer_export` (MCP) or `octopus-api-connector transfer` (CLI) builds a package per fiscal year with **read-only** access to Octopus. Dutch: [DOSSIER-TRANSFER.nl.md](DOSSIER-TRANSFER.nl.md).

## Two steps
1. **Estimate** (`octopus_dossier_transfer_schatting` or `transfer` without `--yes`): number of calls per endpoint compared with today's remaining daily limit. Master data (accounts per bookyear, relations, VAT codes) may only be fetched **2 times a day**, so a multi-year transfer can take more than one day.
2. **Export** (`bevestig=true` / `--yes`): writes the package. If a daily limit is reached, the parts already exported are kept in a checkpoint; run the same command again later (for example tomorrow) to resume.

## Package contents
| Path | Contents |
|---|---|
| `dossier/relaties`, `btw-codes`, `kostenplaatsen`, `boekjaren` | Dossier master data |
| `boekjaar-<id>/boekjaar`, `dagboeken` | Fiscal year and journals |
| `boekjaar-<id>/rekeningschema` | Chart of accounts as returned by Octopus (Belgian MAR/PCMN; not renumbered) |
| `boekjaar-<id>/proefbalans-einde` | Trial balance **built** from balances per account per period (Octopus has no trial-balance endpoint) |
| `boekjaar-<id>/boekingslijnen` | All booking lines (omit with `--no-lines`) |
| `boekjaar-<id>/openstaande-klanten-einde`, `-leveranciers-einde` | Open items at year end |
| `CONTROL.md` | Reconciliations: debit = credit, bookings = balances, open items vs. 40/44; deviations are marked AFWIJKING |
| `MANIFEST.json` | Files with row counts and SHA-256 |
| `README.md` | Explanation for the receiving bookkeeper, including professional and GDPR points |

Formats: csv, json, xlsx. Optional `--zip` (not encrypted: encrypt it yourself before sending).

## Limits (verifieer actuele regel)
- The meaning of period balances (movement or cumulative, `OCTOPUS_AMOUNTS_MODE`) and the sign convention must be verified on the demo dossier.
- No fixed-asset register, depreciation tables or attachments via the endpoints used.
- Follow your professional institute's rules for transferring a file and contacting the colleague; the client remains owner of the data. The connector never sends anything itself.
