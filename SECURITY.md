# Security policy

## Reporting a vulnerability
Please do **not** open a public issue for security problems. Use GitHub's private vulnerability reporting ("Security" tab, "Report a vulnerability") on this repository.

Include what you found, how to reproduce it with synthetic data, and the version. Never send real Octopus credentials, the software house UUID or client data.

## Scope
Of particular interest: any way to write to Octopus without `OCTOPUS_WRITE_ENABLED=true` and a valid confirmation code; to reach a host other than `service.inaras.be` or the Management API; to exceed a daily limit without the connector refusing; to leak a password, token, dossier token, software house UUID or cache key into logs, tool output, exports or the quota file; or to read the encrypted store without the cache key.

## Handling secrets
If you ever pasted an Octopus password or software house UUID somewhere by mistake, change the password in Octopus and ask Octopus about the UUID. Tokens expire after 10 minutes.
