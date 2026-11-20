# AGENTS.md

Guidance for AI coding agents and assistants working in this repository.

Intended for Belgian bookkeepers/accountants; based on Belgian accounting and VAT rules (MAR, Belgian VAT system). Use outside Belgium: verify the local rules yourself.

Powered by FISCALCI Accounting & Tax (Askin Alci)

## What this repo is
FISCAi Octopus API Connector: a local MCP server and CLI (Python, stdio) with read-only access to the Octopus REST API (`service.inaras.be/octopus-rest-api/v1`). The shared engine (tokens, quota, cache, sync state, trial balance, export, transfer, automation, hooks) is the FISCAi Accounting API Core, vendored in `server/vendor/accounting_api_core` (do not edit there: change the core and run `scripts/sync_core.py`). Ready-made agent definitions are in [agents/](agents/README.md).

## Layout
- `server/octopus_mcp/`: `client.py` (auth, dossier token, quota, cache, error variants), `endpoints.py` + `spec_endpoints.py` (registry from the official spec), `sync.py` (modified endpoints), `tools.py` / `tooldefs.py` (MCP tools), `transfer.py`, `write.py` (gated), `cli.py`, `server.py`.
- `tests/`: offline suite with `FakeOctopus` (httpx MockTransport) and synthetic `[Voorbeeld]` fixtures. The network is blocked in tests.
- `scripts/`: generators for manifests, Postman, docs, agents and manuals. Generated files must stay in sync (CI checks).

## Rules
- Read-only by default. Never enable or document enabling `OCTOPUS_WRITE_ENABLED` in examples; never add write calls outside `write.py`.
- Never add the Octopus Management API, any paid plan or paid third-party service. Only VIES and ECB as optional free helpers.
- Respect the daily limits: every new tool must declare its endpoints, use the cache/sync where possible and go through the quota check.
- No secrets and no real client data anywhere (code, tests, docs, fixtures). Use `[Voorbeeld]` data. No live Octopus calls in tests or CI.
- Keep tool names (`octopus_*`) stable. Keep the "Powered by" line and the Belgian notice in docs.
- Uncertain API behaviour goes to [docs/OPEN-QUESTIONS.md](docs/OPEN-QUESTIONS.md) and is marked "verifieer actuele regel".
- Run `make test` and `make lint` before proposing changes.
