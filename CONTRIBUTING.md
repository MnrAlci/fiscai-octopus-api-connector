# Contributing

Thanks for your interest. This is a small, safety-first project: it must never write to Octopus unless write mode is explicitly enabled, and it must respect the Octopus daily limits.

## Ground rules
- **No real data.** Tests, fixtures, docs and screenshots use synthetic `[Voorbeeld]` data only. Never commit credentials, `.env` files, logs, Octopus figures or client data.
- **Daily limits first.** A new tool that calls an endpoint with a low limit (2 or 10 per day) must use the cache or the sync layer. The limit comes from `spec/endpoints.json`; never hard-code a higher one.
- **Read-only first.** Write actions only go through `write.py` (two steps, confirmation code, daily maximum). Never add delete operations, the Management API or the file-import API.
- **Uncertain behaviour** is marked `verifieer actuele regel` in code and docs and listed in `docs/OPEN-QUESTIONS.md`.
- **Keep the attribution.** `Powered by FISCALCI Accounting & Tax (Askin Alci)` must stay unchanged (see `NOTICE`); the code checks it.
- **Belgian scope.** Accounting rules follow the Belgian MAR and VAT; say so when you add rules.
- **Shared core.** Changes to `server/vendor/accounting_api_core` belong in the *FISCAi Accounting API Core* repository; copy them with `python scripts/sync_core.py`.

## Development
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider -q tests
.venv/bin/ruff check .
```
All tests use a mocked Octopus API (`tests/conftest.py`); no Octopus call is made and network access is blocked during the tests.

After changing tools, regenerate the docs and manifests: `python scripts/build_docs.py && python scripts/build_manifests.py && python scripts/build_postman.py`.

## Pull requests
Open an issue first for larger changes. Describe what changes and add tests. By contributing you agree that your contribution is licensed under Apache-2.0.
