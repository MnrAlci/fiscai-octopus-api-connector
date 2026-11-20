# Changelog

All notable changes are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/) and the project uses [semantic versioning](https://semver.org/).

## [1.0.0] - 2026-11-20

### Added
- Release packaging: reproducible `.mcpb` bundle (`scripts/build_mcpb.py`), registry metadata (`server.json`, type `mcpb`), release checklist in `docs/maintainers/RELEASE.md`.

### Changed
- Version 1.0.0. Registry metadata no longer points to PyPI; the bundle is distributed through the GitHub release.
- Dependabot configuration: grouped weekly updates with commit prefixes.

### Notes
- Tested offline against a mocked API built from the official specification. Not yet validated against a live Octopus dossier (see `docs/OPEN-QUESTIONS.md`).

## [0.1.0] - 2026-11-20

### Added
- First version of FISCAi Octopus API Connector: local MCP server (stdio) and CLI `octopus-api-connector` for the Octopus REST API (`service.inaras.be/octopus-rest-api/v1`).
- 49 read-only tools; 2 write tools only with `OCTOPUS_WRITE_ENABLED=true` (two steps, confirmation code, daily maximum, no deletes).
- Endpoint registry and daily limits generated from the official OpenAPI specification (78 paths, 103 operations).
- Daily-limit counter per endpoint (Europe/Brussels), checked before every call; cache with lifetimes based on the limit.
- Automatic refresh of the 10-minute authentication and dossier tokens; one retry on HTTP 401.
- Local sync through the modified-since endpoints (accounts, balances, relations, bookings), encrypted with `OCTOPUS_CACHE_KEY` or memory only.
- Trial balance built from accounts and balances per period; ageing and MAR key figures.
- Both error-object variants (`errorCode/errorMessage/technicalInfo` and `octopusErrorCode/description/technicalDescription`).
- Export (CSV, JSON, xlsx, Parquet), dossier transfer per fiscal year (CONTROL.md, MANIFEST.json with SHA-256, resumable), hooks and automation from the shared core.
- Optional free helpers: Belgian VAT-number check (modulo 97, VIES) and ECB reference rates.
- Postman collection (read operations only), manuals NL/EN (MD, PDF, DOCX), agent definitions, CI, rulesets.
- Unresolved `${OCTOPUS_*}` placeholders from MCP clients that do not expand variables count as unset (defaults apply, write mode stays off).
- The MCP server checks the attribution at start-up; JSON exports and the transfer README are refused without the exact attribution.
