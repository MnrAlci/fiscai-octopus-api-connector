# spec/

`endpoints.json` is **generated** by `scripts/build_endpoints.py` from the public, official OpenAPI 3 specification of the Octopus REST API:

- https://service.inaras.be/octopus-rest-api/v1/openapi.json (Swagger UI: https://service.inaras.be/octopus-rest-api/v1/swagger-ui.html)

It contains only facts the connector needs: method, path, summary, read/write classification, the daily limit from the
"Maximum allowed calls per day" text of each operation, parameter names and the request-body schema name. The full
specification itself is not redistributed here (verifieer actuele regel: redistribution terms of the specification).

Regenerate after Octopus publishes a new version:

```bash
curl -fsS -o /tmp/octopus-rest-api.openapi.json https://service.inaras.be/octopus-rest-api/v1/openapi.json
python scripts/build_endpoints.py /tmp/octopus-rest-api.openapi.json
python scripts/build_postman.py
python -m pytest tests -q
```

The tests (`tests/test_endpoints.py`) fail when the registry in `server/octopus_mcp/endpoints.py` refers to an operation
that no longer exists, or when a daily limit changes.

The connector never uses the Octopus **Management API** or the **file import/file sync API**, and no paid plan.
