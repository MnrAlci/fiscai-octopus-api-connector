# Write mode (off by default)

> Intended for Belgian bookkeepers/accountants; based on Belgian accounting and VAT rules (MAR, Belgian VAT system). Use outside Belgium: verify the local rules yourself.
>
> Powered by FISCALCI Accounting & Tax (Askin Alci)

The connector is **read-only by default**. Write tools do not exist in the tool list unless `OCTOPUS_WRITE_ENABLED=true`. Only turn this on after a deliberate decision, preferably on the Octopus demo dossier first (there is no sandbox).

## Allowed actions
Only these REST operations from the official specification can be used; everything else is refused:

| `actie` | Endpoint |
|---|---|
| `relatie_bijwerken` | `PUT /dossiers/{dossierId}/relations` |
| `aankoop_verkoop_aanmaken` / `_bijwerken` | `POST` / `PUT /dossiers/{dossierId}/buysellbookings` |
| `financieel_divers_aanmaken` / `_bijwerken` | `POST` / `PUT /dossiers/{dossierId}/financialdiversbookings` |
| `afpunting_toevoegen` | `POST /dossiers/{dossierId}/balancings` |

Deleting, closing bookyears, the Management API and anything that could cause costs are never offered.

## Two steps
1. `octopus_schrijf_voorstel` shows exactly what would be sent (endpoint, dossier, body, check digest) and returns a confirmation code valid for 10 minutes. **Nothing is sent.**
2. `octopus_schrijf_bevestigen` sends that exact proposal. Limits: `OCTOPUS_WRITE_MAX_PER_DAY` (default 20), the Octopus daily limit of the endpoint (for example 10/day for buy/sell bookings), and `OCTOPUS_ALLOWED_DOSSIERS`.

The command line (`octopus-api-connector call`) always refuses write tools. MCP clients see `readOnlyHint: false` and `destructiveHint: true` on the confirm tool, so they ask for approval.

## Your responsibility
A booking in Octopus is part of the client's accounting. Check accounts (MAR), VAT codes and amounts yourself; verifieer actuele regel for the body format in the official specification ([OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)).
