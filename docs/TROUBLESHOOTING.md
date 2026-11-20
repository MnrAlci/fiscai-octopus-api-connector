# Troubleshooting

> Intended for Belgian bookkeepers/accountants; based on Belgian accounting and VAT rules (MAR, Belgian VAT system). Use outside Belgium: verify the local rules yourself.
>
> Powered by FISCALCI Accounting & Tax (Askin Alci)

| Symptom | Cause and fix |
|---|---|
| `doctor` reports missing credentials | Set `OCTOPUS_SOFTWARE_HOUSE_UUID`, `OCTOPUS_USER`, `OCTOPUS_PASSWORD` in the client environment. |
| "OCTOPUS_BASE_URL moet https zijn op service.inaras.be" | Only the official REST API is allowed; remove the variable or set the default. The Management API is refused on purpose. |
| Exit code 6 / "daglimiet bereikt" | The endpoint's daily limit is used up. Wait for the reset time shown, use cached data, or plan the next sync. Check `quota`. |
| Every restart costs calls again | Set `OCTOPUS_CACHE_KEY` (16+ characters) so cache and sync are stored encrypted. |
| 401 after some minutes | Tokens are valid 10 minutes; the connector renews them. If it persists, the user/password or the web-service module access is wrong. |
| Trial balance not in balance or figures look cumulative | Check `OCTOPUS_AMOUNTS_MODE` (movement/cumulative) on the demo dossier; verifieer actuele regel ([OPEN-QUESTIONS.md](OPEN-QUESTIONS.md)). |
| "dossier niet toegelaten" | The dossier is not in `OCTOPUS_ALLOWED_DOSSIERS`. |
| Write tools are missing | Expected: write mode is off ([WRITE.md](WRITE.md)). |
| Error text in another language | Set `OCTOPUS_LOCALE_ID` (1 NL, 2 FR, 3 EN, 4 DE). |

When reporting a bug, include `octopus-api-connector doctor --json` (contains no secrets) and never client data.
