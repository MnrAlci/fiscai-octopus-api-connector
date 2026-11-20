# Operations: daily limits, cache, sync and tokens

> Intended for Belgian bookkeepers/accountants; based on Belgian accounting and VAT rules (MAR, Belgian VAT system). Use outside Belgium: verify the local rules yourself.
>
> Powered by FISCALCI Accounting & Tax (Askin Alci)

## Daily limits
Octopus limits calls **per endpoint per day**, some as low as 2 (accounts, VAT codes, currencies, cost centres, custom fields, products, product groups, relations without search). The connector keeps a local counter (`quota.json` in `OCTOPUS_DATA_DIR`, no dossier ids) and **refuses before sending** when a limit would be exceeded, with the reset time. The counter is per method + path for all dossiers together (conservative; verifieer actuele regel). `octopus-api-connector quota` or the tool `octopus_quota` show the status. Calls you make outside the connector (Postman, other software) are not counted: keep a reserve with `OCTOPUS_QUOTA_RESERVE`.

## Cache and sync
- With `OCTOPUS_CACHE_KEY` the cache and sync state are stored encrypted on disk; without it they live only in memory (each process restart then costs calls again).
- The first sync loads per bookyear and journal type from `1980-01-01 00:00:00.000`; later syncs use the modified endpoints with `bookyearId=-1` / `journalTypeId=-1` and the stored watermark (Europe/Brussels time). Deleted bookings are removed by their DocumentKey.
- `octopus_sync_status` shows when each part was last synced. `cache clear` removes cache and sync (the next sync is a full load again).

## Tokens
The authentication token and the dossier token are valid for 10 minutes. The connector renews them automatically shortly before expiry and once more on a 401; tokens are only kept in memory.

## Errors
Octopus returns two error-object variants (`errorCode/errorMessage/technicalInfo` in the specification, `octopusErrorCode/description/technicalDescription` in the manual) or plain text. Both are normalised and scrubbed of tokens and credentials. `octopus_foutcode_uitleg` explains an error code (uses `/error`, 100/day).

## No pagination
Octopus returns full lists. Large dossiers are handled by the sync (incremental) and by limiting what the tools return (`max_rijen`, default 200; exports always write everything).
