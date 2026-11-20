# Open questions (verifieer actuele regel)

The connector is built only on points marked **BEVESTIGD** in the FISCAi knowledge bundle (Kennisonderzoeker, SharePoint) and on the public official specification at `service.inaras.be`. Everything below is **ONZEKER** (uncertain) or **CONFLICT** in that bundle, or an interpretation the connector had to make. In code and tool output these points carry the note *verifieer actuele regel*. Check them on the Octopus demo dossier before production use (there is no sandbox).

Status per point: what the connector does today, and what would change if the answer is different.

## From the knowledge bundle (Octopus REST API)

| Point | Status | Question | What the connector does now |
|---|---|---|---|
| T6 | ONZEKER | How an OAuth access token is passed to the REST API (`Token` header or `Authorization: Bearer`). The REST spec has no securityScheme; the Management spec uses Bearer. | No OAuth. Only the documented flow: `POST /authentication` with header `softwareHouseUuid` and body `{user, password}`. OAuth is on the roadmap. |
| T7 | CONFLICT | Header is `Token` (capital) in the spec; another source writes `token`. | Sends `Token` exactly as in the spec (HTTP header names are case-insensitive, so both should work). |
| T8 | CONFLICT | The manual calls the API "sessionless and stateless" but also says "session cookies must be enabled". | The HTTP client keeps cookies on (harmless if unused) and never depends on them. |
| T9 | ONZEKER | Whether `Accept: application/json` is mandatory. | Always sends `Accept: application/json`; `Content-Type: application/json` only with a body. |
| T12 | CONFLICT | Fields "account type" and "currency" in `AccountServiceData` (not in the spec). | Not used. The account class and kind (balance/costs/revenue) are derived from the MAR account number. |
| T13 | ONZEKER | Whether a separate trial-balance endpoint exists (none found). | Builds the trial balance from `GET /accounts` and `GET /accounts/amounts/modified`. If an endpoint appears, it can replace the builder. |
| T17 | ONZEKER | Maximum number of items per response or per array (the API has no pagination). | Reads whatever comes back in one response; tools cap what they show (`max_rijen`, default 200), exports contain everything. |
| T19 | ONZEKER | HTTP status when a daily limit is exceeded (429 / `Retry-After`); the manual mentions a warning e-mail. | Never relies on it: the connector counts every call itself and refuses before sending. An unexpected 429 is reported as an API error; no automatic retry. |
| T20 | CONFLICT | Error object: manual `{octopusErrorCode, description, technicalDescription}` versus spec `ErrorResult{errorCode, errorMessage, technicalInfo}`. | Parses both variants (and plain text) and reports which variant it saw (`variant`: `spec`, `manual` or `none`). |
| T22 | ONZEKER | A list of error codes ("article under construction"). | `octopus_foutcode_uitleg` asks the sample object from `GET /error` (100/day); the connector adds only generic hints per HTTP status. |
| T26 | ONZEKER | A separate sandbox URL, and whether the demo dossier is free or unlimited in time. | No sandbox URL is configured; the only allowed host is `service.inaras.be`. Test on the demo dossier only after confirming with Octopus that it is free. |

## From the knowledge bundle (free helpers)

| Point | Status | Question | What the connector does now |
|---|---|---|---|
| A16 | ONZEKER | VIES fair use and throttling. | VIES is optional, one call per explicit request, no batch, no retry. |
| A18 | ONZEKER | ECB publication time (around 16:00 CET) and "for information only". | Shows the date of the rate returned; labels it "for information". |

No Apilayer service is used: they need an API key and the useful volumes are paid. VIES (European Commission) and the ECB data portal are free and keyless.

## Interpretations made by the connector

| Topic | Interpretation | How to verify |
|---|---|---|
| Balances per period | `accounts/amounts/modified` returns a **movement** per period (`OCTOPUS_AMOUNTS_MODE=movement`). With `cumulative` the builder takes the last period instead. | Run a dossier transfer: the check "sum of booking lines per account = trial balance" in `CONTROL.md` passes only with the right mode (for a year without opening entries). |
| Sign | `balance` > 0 is debit (trial balance shows `saldo = debet - credit`). | Compare one account with the Octopus screen. |
| Account number | `accountKey.id` is the MAR account number (as text, e.g. `400000`). | Compare the chart of accounts with Octopus. |
| Open items | `openBookingAmount` is the open amount in EUR, positive for a normal receivable (customers) or payable (suppliers); lines with 0 are skipped. The period range is the first period of the first fiscal year to the last period of the last one. | Compare `octopus_openstaande_posten` with the open-items report in Octopus. |
| Deleted bookings | `deletedBookings` contains `DocumentKey{bookyearKey, journalType, journalSequenceNr, documentSequenceNr}`; `journalSequenceNr` is matched with `journalNr` of the booking lines. | Delete a test document in the demo dossier and sync. |
| Watermark | The next sync uses the start time of the previous sync minus 120 seconds (overlap), in local time (Europe/Brussels), format `YYYY-MM-DD HH:MM:SS.000`. The server time zone is not documented. | Change a booking and sync twice. |
| Daily limits | Counted per method + path (e.g. `GET /dossiers/{dossierId}/accounts`), per day in Europe/Brussels, across all dossiers. Octopus may count per dossier or per user; counting across dossiers is the safe side. Relations with a search term count separately (400/day). | Ask Octopus how the limits are counted. |
| Initial relations | The first sync uses `GET /relations` (probably only active relations), then `relations/modified`. | Compare the number of relations with Octopus. |
| Tokens | Auth token and dossier token both valid 10 minutes; renewed 60 s early; one retry on HTTP 401 with fresh tokens. | Covered by the specification; behaviour on the live API to be observed. |
| `localeId` | Default 1 for the dossier token (values 0-4). Which value is Dutch is not documented clearly. | Try on the demo dossier. |
| Header typo in the spec | One header in the specification is spelled `documentSequennceNr` (write/attachment operations, not used by the read tools). | Check when attachments are added. |
| Specification redistribution | Only a derived endpoint list (`spec/endpoints.json`) and a Postman collection are shipped, not the full OpenAPI file. | Check the terms with Octopus before publishing. |

## Not used on purpose

- The **Management API** (paid), the **file-import** and **file-sync** APIs, and any paid plan.
- Write operations other than the six in `docs/WRITE.md`; never deletes.

Powered by FISCALCI Accounting & Tax (Askin Alci)
