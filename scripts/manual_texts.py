"""Teksten van de volledige handleidingen (EN en NL). {be}, {attr}, {n}, {ro} en {tools} worden ingevuld door build_manuals.py."""

MAN_EN = """# FISCAi Octopus API Connector: complete manual

> {be}
>
> {attr}

This manual explains every feature step by step. The connector is a plugin for Grok Bot (it also works in Copilot, Claude, Cursor, Windsurf and other MCP clients) and a command-line tool that reads your Octopus accounting data locally with your own Octopus user. It is **read-only by default**, uses only the free Octopus REST API (`https://service.inaras.be/octopus-rest-api/v1`) and is not an official Octopus product. Never the Management API, never a paid plan.

## 1. What you need
1. Python 3.10 or higher.
2. An Octopus user with access to the web-service module, and a **Software House ID** (UUID) requested from Octopus.
3. There is no sandbox: test first on the Octopus **demo dossier**.

## 2. Install and first run
1. Get the code and install it: `git clone <repository-url> fiscai-octopus-api-connector`, `cd fiscai-octopus-api-connector`, `python3 -m venv .venv`, `.venv/bin/pip install .`
2. `octopus-api-connector config init` writes an example `.env` with placeholders only. Fill `OCTOPUS_SOFTWARE_HOUSE_UUID`, `OCTOPUS_USER` and `OCTOPUS_PASSWORD` in your environment or your client's secret settings; never in a chat or the repository.
3. Set `OCTOPUS_CACHE_KEY` (at least 16 characters). It enables the encrypted cache and sync on disk; without it every restart costs calls again.
4. `octopus-api-connector doctor` checks Python, packages, configuration and write mode. It makes no call and prints no secrets.
5. In Grok Bot or another MCP client, ask: "Run `octopus_status`". This makes no Octopus call.

## 3. Daily limits: the most important rule
Octopus limits calls **per endpoint per day**. Some endpoints allow only **2 calls a day** (accounts, VAT codes, currencies, cost centres, custom fields, products, product groups, relations without search), buy/sell and financial/diverse bookings 10, bookyears/journals/reports 24, the modified endpoints 48, dossiers 150, invoices and relations with search 400.

1. The connector counts every call in a local file (no dossier ids) and **refuses before sending** when a limit would be exceeded. It shows the reset time.
2. Check `octopus_quota` (or `octopus-api-connector quota`) before heavy work.
3. Use `octopus_sync` once, then work with the local tools. `vers: true` forces a new call: only when needed.
4. Calls you make elsewhere (Postman, other software) are not counted; keep a reserve with `OCTOPUS_QUOTA_RESERVE`.
5. Tokens are valid 10 minutes and are renewed automatically. Octopus has no pagination: lists come complete and tool output is capped with `max_rijen`.

## 4. Use it from an assistant
1. **Grok Bot**: install the plugin and ask in plain language: "Give me the trial balance of dossier [Voorbeeld] for 2026 up to period 6."
2. **Other MCP clients**: copy a file from `examples/` (Cursor, Claude Desktop, Claude Code, VS Code, Windsurf, generic stdio) and use the client's secret handling.
3. **Agents**: ready-made definitions are in `agents/` (section 12).

## 5. The tools, grouped by domain
There are {n} tools (`octopus_*`): {ro} read-only or local tools, and 2 write tools that only exist when write mode is enabled (section 13).

{tools}

## 6. Sync, trial balance and key figures
1. `octopus_dossiers`, then `octopus_boekjaren` for the dossier.
2. `octopus_sync` (or `octopus-api-connector sync --dossier <id>`): the first time it loads everything per bookyear and journal type; afterwards only changes via the modified endpoints. Deleted bookings are removed. `octopus_sync_status` shows the watermarks.
3. `octopus_proefbalans`: Octopus has no trial-balance endpoint, so the connector **builds** it from the chart of accounts and the balances per account per period. Balance = debit minus credit (revenue is negative); it checks debit = credit and totals per MAR class.
4. Whether period balances are movements or cumulative (`OCTOPUS_AMOUNTS_MODE`) and the sign convention must be verified on the demo dossier: verifieer actuele regel.
5. `octopus_openstaande_posten` and `octopus_ouderdom_openstaande_posten` (customers or suppliers, reference date). A negative open amount is an item to check, not a conclusion.
6. `octopus_dashboard_kpis`: revenue, costs, result, margin, liquid assets, open items, DSO/DPO, for a year, a month (`maand:5`) or a quarter (`kwartaal:2`).

## 7. Export layer (CSV, JSON, xlsx, Parquet)
1. `octopus-api-connector export proefbalans --dossier <id> --out ./export --format csv --format xlsx` or the tool `octopus_export_dataset`.
2. Datasets: `kpis`, `saldi`, `proefbalans`, `openstaande_posten` (with `--kind debiteuren|crediteuren`), `boekingslijnen`, `rekeningschema`, `relaties`. Fixed schema: `docs/EXPORT-SCHEMA.md`. Parquet needs the optional `pyarrow`.
3. Let Excel, Power BI or other tools read the files instead of calling the connector repeatedly.

## 8. Command line
| Command | Purpose |
|---|---|
| `serve` | start the MCP server (stdio) |
| `doctor` | check the environment (no calls) |
| `tools`, `call TOOL name=value` | list tools; call one read-only tool |
| `sync`, `quota`, `cache status|clear` | sync, daily limits, local cache |
| `export`, `transfer` | exports and dossier transfer |
| `workflows init|list|plan|run` | automation |
| `config init`, `version`, `completion` | configuration, version, shell completion |

Common options: `--json`, `--quiet`, `--verbose`, `--log-level`, `--log-format json`, `--env-file`, `--hooks`, `--dry-run`, `--data-dir`. Exit codes: 0 ok, 1 error, 2 usage, 3 configuration, 4 tool/Octopus error, 5 network, 6 refused (daily limit, write tool, dossier not allowed). Details: `docs/CLI.md`.

## 9. Hooks (optional, off by default)
1. Copy `examples/hooks/hooks.example.toml` and set `enabled = true`.
2. Events: `pre_call`, `post_call`, `on_error`, `on_export`, each with a local command (list, no shell) or a Python function.
3. Start with `--hooks FILE` or `OCTOPUS_HOOKS_FILE`. Hooks never receive secrets and never break a call. Details: `docs/HOOKS.md`.

## 10. Automation
1. `octopus-api-connector workflows init --path workflows.toml` writes an example with `[Voorbeeld]` data; each client needs `dossier_id`.
2. `workflows plan` shows what is due (no Octopus calls); `workflows run` writes overviews per meeting and per due obligation, and **draft** e-mails (`.eml`).
3. Deadlines in the example are examples marked "verifieer actuele regel". Mails are never sent by default.
4. Schedule with cron, Windows Task Scheduler, n8n or GitHub Actions (`examples/workflows/`); keep the cache on a persistent machine to save the daily limits. Details: `docs/AUTOMATION.md`.

## 11. Dossier transfer per fiscal year
1. Estimate: `octopus-api-connector transfer --dossier <id> --out ./overdracht` (without `--yes`) shows the calls per endpoint against today's limits.
2. Run with `--yes` (optionally `--bookyear` per year, `--no-lines`, `--zip`). Master data may be fetched only twice a day, so a multi-year transfer can take more than one day: repeat the command later and it resumes from the checkpoint.
3. Read `CONTROL.md`, `MANIFEST.json` (SHA-256) and the `README.md` for the receiving bookkeeper.
4. Hand over securely and observe the professional, GDPR and retention points (verifieer actuele regel). Details: `docs/DOSSIER-TRANSFER.md`.

## 12. Agents, Postman and integrations
- **Agents**: `agents/README.md` lists Grok Bot, Claude Code, Claude Desktop, GitHub Copilot, Cursor and a generic system prompt. Nothing is installed for you.
- **Postman**: import the collection and environment from `postman/`; it contains only the 50 read operations. Every request counts towards the daily limits and is not counted by the connector (`docs/POSTMAN.md`).
- **Integrations**: `docs/integrations/README.md`.

## 13. Write mode (off by default)
Only with `OCTOPUS_WRITE_ENABLED=true`. Two steps: `octopus_schrijf_voorstel` shows exactly what would be sent and returns a code valid 10 minutes; `octopus_schrijf_bevestigen` sends it. Only six actions are possible (update relation, create/update buy-sell booking, create/update financial-diverse booking, add balancing); never delete. Maximum `OCTOPUS_WRITE_MAX_PER_DAY` (default 20). The command line always refuses write tools. Read `docs/WRITE.md` first; most users never enable it.

## 14. Free helpers
`octopus_btw_nummer_controle` checks a VAT number with the Belgian check digit and optionally VIES; `octopus_wisselkoers_ecb` gives ECB reference rates. Both are free public services and only called when you use them.

## 15. Privacy, open questions and help
- Data stays on your computer; what the assistant sees goes to the model provider you chose (`docs/PRIVACY-DATA-FLOW.md`).
- Points not yet confirmed (amounts mode, sign, limits counting, error format) are listed in `docs/OPEN-QUESTIONS.md`: verifieer actuele regel.
- Not tax or legal advice: have figures reviewed by your bookkeeper/accountant.
- Problems: `docs/TROUBLESHOOTING.md`; run `octopus-api-connector doctor`.

{attr}
"""

MAN_NL = """# FISCAi Octopus API Connector: volledige handleiding

> {be}
>
> {attr}

Deze handleiding legt elke functie stap voor stap uit. De connector is een plugin voor Grok Bot (werkt ook in Copilot, Claude, Cursor, Windsurf en andere MCP-clients) en een opdrachtregeltool die uw Octopus-boekhouding lokaal leest met uw eigen Octopus-gebruiker. Hij is **standaard alleen-lezen**, gebruikt alleen de gratis Octopus REST API (`https://service.inaras.be/octopus-rest-api/v1`) en is geen officieel Octopus-product. Nooit de Management API, nooit een betalend plan.

## 1. Wat u nodig heeft
1. Python 3.10 of hoger.
2. Een Octopus-gebruiker met toegang tot de webservicemodule, en een **Software House ID** (UUID) aangevraagd bij Octopus.
3. Er is geen sandbox: test eerst op het **demodossier** van Octopus.

## 2. Installeren en eerste start
1. Code ophalen en installeren: `git clone <repository-url> fiscai-octopus-api-connector`, `cd fiscai-octopus-api-connector`, `python3 -m venv .venv`, `.venv/bin/pip install .`
2. `octopus-api-connector config init` schrijft een voorbeeld-`.env` met alleen plaatshouders. Vul `OCTOPUS_SOFTWARE_HOUSE_UUID`, `OCTOPUS_USER` en `OCTOPUS_PASSWORD` in uw omgeving of in de geheime instellingen van uw client in; nooit in een chat of in de repository.
3. Zet `OCTOPUS_CACHE_KEY` (minstens 16 tekens). Daarmee worden cache en synchronisatie versleuteld op schijf bewaard; zonder sleutel kost elke herstart opnieuw calls.
4. `octopus-api-connector doctor` controleert Python, pakketten, configuratie en schrijfmodus. Doet geen call en toont geen geheimen.
5. Vraag in Grok Bot of een andere MCP-client: "Voer `octopus_status` uit". Dat doet geen Octopus-call.

## 3. Daglimieten: de belangrijkste regel
Octopus beperkt het aantal calls **per endpoint per dag**. Sommige endpoints laten maar **2 calls per dag** toe (rekeningen, btw-codes, munten, kostenplaatsen, vrije velden, producten, productgroepen, relaties zonder zoekterm), aankoop/verkoop- en financiële/diverse boekingen 10, boekjaren/dagboeken/rapporten 24, de gewijzigde-endpoints 48, dossiers 150, facturen en relaties met zoekterm 400.

1. De connector telt elke call in een lokaal bestand (zonder dossier-id's) en **weigert vóór het versturen** als een limiet overschreden zou worden. Hij toont het resettijdstip.
2. Kijk `octopus_quota` (of `octopus-api-connector quota`) na vóór groot werk.
3. Gebruik één keer `octopus_sync` en werk daarna met de lokale tools. `vers: true` dwingt een nieuwe call af: alleen als het nodig is.
4. Calls die u elders doet (Postman, andere software) worden niet geteld; houd een reserve met `OCTOPUS_QUOTA_RESERVE`.
5. Tokens zijn 10 minuten geldig en worden automatisch vernieuwd. Octopus kent geen paginering: lijsten komen volledig en de tooluitvoer wordt begrensd met `max_rijen`.

## 4. Gebruik vanuit een assistent
1. **Grok Bot**: installeer de plugin en vraag in gewone taal: "Geef de proefbalans van dossier [Voorbeeld] voor 2026 tot en met periode 6."
2. **Andere MCP-clients**: kopieer een bestand uit `examples/` (Cursor, Claude Desktop, Claude Code, VS Code, Windsurf, generieke stdio) en gebruik het geheimenbeheer van de client.
3. **Agents**: kant-en-klare definities staan in `agents/` (hoofdstuk 12).

## 5. De tools per domein
Er zijn {n} tools (`octopus_*`): {ro} alleen-lezen of lokale tools, en 2 schrijftools die alleen bestaan als de schrijfmodus aan staat (hoofdstuk 13).

{tools}

## 6. Synchronisatie, proefbalans en kerncijfers
1. `octopus_dossiers`, daarna `octopus_boekjaren` voor het dossier.
2. `octopus_sync` (of `octopus-api-connector sync --dossier <id>`): de eerste keer laadt hij alles per boekjaar en dagboektype; daarna alleen wijzigingen via de gewijzigde-endpoints. Verwijderde boekingen worden weggehaald. `octopus_sync_status` toont de watermerken.
3. `octopus_proefbalans`: Octopus heeft geen proefbalans-endpoint; de connector **stelt ze samen** uit het rekeningschema en de saldi per rekening per periode. Saldo = debet min credit (opbrengsten zijn negatief); hij controleert debet = credit en totalen per MAR-klasse.
4. Of periodesaldi bewegingen of cumulatief zijn (`OCTOPUS_AMOUNTS_MODE`) en de tekenconventie: te verifiëren op het demodossier (verifieer actuele regel).
5. `octopus_openstaande_posten` en `octopus_ouderdom_openstaande_posten` (klanten of leveranciers, peildatum). Een negatief openstaand bedrag is na te gaan, geen conclusie.
6. `octopus_dashboard_kpis`: omzet, kosten, resultaat, marge, liquide middelen, openstaande posten, DSO/DPO, voor een jaar, een maand (`maand:5`) of een kwartaal (`kwartaal:2`).

## 7. Exportlaag (CSV, JSON, xlsx, Parquet)
1. `octopus-api-connector export proefbalans --dossier <id> --out ./export --format csv --format xlsx` of de tool `octopus_export_dataset`.
2. Datasets: `kpis`, `saldi`, `proefbalans`, `openstaande_posten` (met `--kind debiteuren|crediteuren`), `boekingslijnen`, `rekeningschema`, `relaties`. Vast schema: `docs/EXPORT-SCHEMA.md`. Parquet vraagt het optionele `pyarrow`.
3. Laat Excel, Power BI of andere tools de bestanden lezen in plaats van de connector telkens aan te roepen.

## 8. Opdrachtregel
| Opdracht | Doel |
|---|---|
| `serve` | MCP-server starten (stdio) |
| `doctor` | omgeving controleren (geen calls) |
| `tools`, `call TOOL naam=waarde` | tools oplijsten; één alleen-lezen tool aanroepen |
| `sync`, `quota`, `cache status|clear` | synchronisatie, daglimieten, lokale cache |
| `export`, `transfer` | exports en dossieroverdracht |
| `workflows init|list|plan|run` | automatisering |
| `config init`, `version`, `completion` | configuratie, versie, shell-aanvulling |

Gemeenschappelijke opties: `--json`, `--quiet`, `--verbose`, `--log-level`, `--log-format json`, `--env-file`, `--hooks`, `--dry-run`, `--data-dir`. Afsluitcodes: 0 ok, 1 fout, 2 gebruik, 3 configuratie, 4 tool/Octopus, 5 netwerk, 6 geweigerd (daglimiet, schrijftool, dossier niet toegelaten). Details: `docs/CLI.nl.md`.

## 9. Hooks (optioneel, standaard uit)
1. Kopieer `examples/hooks/hooks.example.toml` en zet `enabled = true`.
2. Gebeurtenissen: `pre_call`, `post_call`, `on_error`, `on_export`, elk met een lokale opdracht (lijst, geen shell) of een Python-functie.
3. Start met `--hooks BESTAND` of `OCTOPUS_HOOKS_FILE`. Hooks krijgen nooit geheimen en breken nooit een call. Details: `docs/HOOKS.nl.md`.

## 10. Automatisering
1. `octopus-api-connector workflows init --path workflows.toml` schrijft een voorbeeld met `[Voorbeeld]`-gegevens; elke klant heeft een `dossier_id` nodig.
2. `workflows plan` toont wat eraan komt (geen Octopus-calls); `workflows run` schrijft overzichten per vergadering en per verplichting, en **concept**-e-mails (`.eml`).
3. Termijnen in het voorbeeld zijn voorbeelden met "verifieer actuele regel". Mails worden standaard nooit verstuurd.
4. Plan met cron, Windows Taakplanner, n8n of GitHub Actions (`examples/workflows/`); bewaar de cache op een vaste machine om de daglimieten te sparen. Details: `docs/AUTOMATION.nl.md`.

## 11. Dossieroverdracht per boekjaar
1. Schatting: `octopus-api-connector transfer --dossier <id> --out ./overdracht` (zonder `--yes`) toont de calls per endpoint tegenover de limieten van vandaag.
2. Uitvoeren met `--yes` (optioneel `--bookyear` per jaar, `--no-lines`, `--zip`). Stamdata mogen maar twee keer per dag; een overdracht van meerdere jaren kan dus meer dan één dag duren: herhaal de opdracht later en hij hervat via het checkpoint.
3. Lees `CONTROL.md`, `MANIFEST.json` (SHA-256) en de `README.md` voor de ontvangende boekhouder.
4. Maak veilig over en volg de deontologische, GDPR- en bewaarregels (verifieer actuele regel). Details: `docs/DOSSIER-TRANSFER.nl.md`.

## 12. Agents, Postman en integraties
- **Agents**: `agents/README.md` beschrijft Grok Bot, Claude Code, Claude Desktop, GitHub Copilot, Cursor en een generieke systeemprompt. Er wordt niets voor u geïnstalleerd.
- **Postman**: importeer collectie en omgeving uit `postman/`; ze bevat alleen de 50 leesoperaties. Elk verzoek telt mee voor de daglimieten en wordt niet geteld door de connector (`docs/POSTMAN.nl.md`).
- **Integraties**: `docs/integrations/README.nl.md`.

## 13. Schrijfmodus (standaard uit)
Alleen met `OCTOPUS_WRITE_ENABLED=true`. Twee stappen: `octopus_schrijf_voorstel` toont exact wat verstuurd zou worden en geeft een code die 10 minuten geldig is; `octopus_schrijf_bevestigen` verstuurt het. Slechts zes acties zijn mogelijk (relatie bijwerken, aankoop/verkoopboeking aanmaken/bijwerken, financiële/diverse boeking aanmaken/bijwerken, afpunting toevoegen); nooit verwijderen. Maximaal `OCTOPUS_WRITE_MAX_PER_DAY` (standaard 20). De opdrachtregel weigert schrijftools altijd. Lees eerst `docs/WRITE.md`; de meeste gebruikers zetten dit nooit aan.

## 14. Gratis hulpdiensten
`octopus_btw_nummer_controle` controleert een btw-nummer met het Belgische controlecijfer en optioneel VIES; `octopus_wisselkoers_ecb` geeft ECB-referentiekoersen. Beide zijn gratis publieke diensten en worden alleen aangeroepen als u ze gebruikt.

## 15. Privacy, open vragen en hulp
- Gegevens blijven op uw computer; wat de assistent ziet gaat naar de modelaanbieder die u koos (`docs/PRIVACY-DATA-FLOW.md`).
- Punten die nog niet bevestigd zijn (saldimodus, teken, telling van limieten, foutformaat) staan in `docs/OPEN-QUESTIONS.md`: verifieer actuele regel.
- Geen fiscaal of juridisch advies: laat de cijfers nakijken door uw boekhouder/accountant.
- Problemen: `docs/TROUBLESHOOTING.md`; voer `octopus-api-connector doctor` uit.

{attr}
"""
