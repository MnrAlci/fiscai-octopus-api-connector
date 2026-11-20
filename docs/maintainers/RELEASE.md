# Release checklist (maintainer)

Nothing here runs automatically. A release needs the owner's explicit approval.

1. `python -m pytest -q` and `ruff check .` pass; CI on `main` is green.
2. Version is the same in `pyproject.toml`, `server/octopus_mcp/__init__.py` and `CHANGELOG.md`; run `python scripts/build_manifests.py`.
3. `python scripts/build_mcpb.py` builds `dist/fiscai-octopus-api-connector-<version>.mcpb` and prints its SHA-256.
4. Put that hash in `scripts/mcpb.sha256`, run `python scripts/build_manifests.py`, commit. (The bundle contains README.md and pyproject.toml, so rebuild after any change to them.)
5. Make the repository public, tag `v<version>`, create the GitHub release and attach the `.mcpb` file (the identifier URL in `server.json` must resolve).
6. Submit to the free marketplaces (MCP Registry, Glama, Cursor, awesome-mcp-servers). No PyPI, no paid plans.

Powered by FISCALCI Accounting & Tax (Askin Alci)
