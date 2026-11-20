# Setup

> Intended for Belgian bookkeepers/accountants; based on Belgian accounting and VAT rules (MAR, Belgian VAT system). Use outside Belgium: verify the local rules yourself.
>
> Powered by FISCALCI Accounting & Tax (Askin Alci)

## 1. What you need
- Python 3.10 or newer.
- An Octopus user with access to the web-service module, and a **Software House ID** (UUID) requested from Octopus. The connector uses only the free REST API at `https://service.inaras.be/octopus-rest-api/v1`; never the Management API or a paid plan.
- No sandbox exists: test first on the Octopus **demo dossier**.

## 2. Install
```bash
pip install .                       # or: pip install -r requirements.txt
octopus-api-connector config init   # writes .env with placeholders only
octopus-api-connector doctor        # no calls, no secrets printed
```

## 3. Configure
Set the values in your environment, a secret manager or a local `.env` that is never committed:

| Variable | Meaning |
|---|---|
| `OCTOPUS_SOFTWARE_HOUSE_UUID`, `OCTOPUS_USER`, `OCTOPUS_PASSWORD` | Credentials (secrets) |
| `OCTOPUS_LOCALE_ID` | Language of Octopus error messages (1 NL, 2 FR, 3 EN, 4 DE) |
| `OCTOPUS_CACHE_KEY` | At least 16 characters; enables the encrypted on-disk cache and sync (strongly advised because of the daily limits) |
| `OCTOPUS_DATA_DIR` | Folder for cache, daily counter and sync state |
| `OCTOPUS_ALLOWED_DOSSIERS` | Optional allow-list of dossier ids |
| `OCTOPUS_QUOTA_RESERVE` | Calls to keep free per endpoint for manual use |
| `OCTOPUS_AMOUNTS_MODE` | `movement` (default) or `cumulative`; verifieer actuele regel |
| `OCTOPUS_WRITE_ENABLED` | Off. See [WRITE.md](WRITE.md) |

## 4. Connect your AI client
Copy one of the files in `examples/` (Cursor, Claude Desktop, Claude Code, VS Code, Windsurf, generic stdio, Grok Bot variables). Put the credentials in the client's environment/secret settings, not in a shared file.

## 5. First sync
```bash
octopus-api-connector call octopus_dossiers
octopus-api-connector sync --dossier <id>
octopus-api-connector quota
```
The first sync loads everything per bookyear; afterwards only changes are fetched through the modified endpoints.
