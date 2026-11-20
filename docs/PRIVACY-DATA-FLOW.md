# Privacy and data flow

> Intended for Belgian bookkeepers/accountants; based on Belgian accounting and VAT rules (MAR, Belgian VAT system). Use outside Belgium: verify the local rules yourself.
>
> Powered by FISCALCI Accounting & Tax (Askin Alci)

| Step | Where the data goes |
|---|---|
| Octopus REST API → connector | HTTPS to `service.inaras.be` only (base URL is locked to that host). |
| Connector → disk | Only if `OCTOPUS_CACHE_KEY` is set: encrypted cache and sync state in `OCTOPUS_DATA_DIR`. Exports and transfer packages are written in clear text where you ask. |
| Connector → AI client | Tool results go to the MCP client you run, and from there to the AI model you chose. Choose a client and model that fits your GDPR obligations. |
| Optional helpers | VIES (EU VAT number check) and ECB exchange rates, both free public services, only when you call those tools. |
| Hooks and workflows | Only what you configure ([HOOKS.md](HOOKS.md), [AUTOMATION.md](AUTOMATION.md)); e-mails are written as drafts (`.eml`), never sent by the connector. |

- No telemetry, no analytics, no third-party calls besides the above.
- Logs and errors are scrubbed of tokens, passwords and the software house UUID.
- You are the controller of your clients' data; this software is a tool. Delete exports and packages you no longer need. See https://www.gegevensbeschermingsautoriteit.be
