# FISCAi Octopus API Connector: volledige handleiding

> Bedoeld voor Belgische boekhouders/accountants; gebaseerd op Belgische boekhoud- en btw-regels (MAR, Belgisch btw-stelsel). Gebruik buiten België: verifieer zelf de lokale regels.
>
> Powered by FISCALCI Accounting & Tax (Askin Alci)

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
Er zijn 51 tools (`octopus_*`): 49 alleen-lezen of lokale tools, en 2 schrijftools die alleen bestaan als de schrijfmodus aan staat (hoofdstuk 13).

### Status en daglimieten (geen Octopus-call)

| Tool | Wat het doet | Octopus-endpoint (daglimiet) |
|---|---|---|
| `octopus_status` | Configuratie (zonder geheimen), daglimieten, cache en versie. Doet geen call naar Octopus. | lokaal |
| `octopus_quota` | Gebruik en resterende calls per Octopus-endpoint vandaag (Europe/Brussels). Doet geen call. | lokaal |
| `octopus_sync_status` | Watermerken en aantallen van de lokale synchronisatie. Doet geen call. | lokaal |
| `octopus_export_schema` | Kolommen en types van de exportdatasets (voor Power BI, Excel, databanken). Doet geen call. | lokaal |

### Sessie, dossiers en boekjaren

| Tool | Wat het doet | Octopus-endpoint (daglimiet) |
|---|---|---|
| `octopus_api_versie` | Versie van de Octopus REST API. | `GET /about/version` |
| `octopus_whoami` | Informatie over de aangemelde Octopus-gebruiker. | `GET /authentication` |
| `octopus_dossiers` | Dossiers waartoe de gebruiker toegang heeft. | `GET /dossiers` (150/dag) |
| `octopus_boekjaren` | Boekjaren met perioden. | `GET /dossiers/{dossierId}/bookyears` (24/dag) |
| `octopus_boekjaar_detail` | Details van één boekjaar. | `GET /dossiers/{dossierId}/bookyears/{bookyearId}` (24/dag) |
| `octopus_boekjaar_status` | Status van een boekjaar: afgesloten, dagboeken, beschermde/afgesloten perioden en synchronisatie. | `GET /dossiers/{dossierId}/bookyears` (24/dag)<br>`GET /dossiers/{dossierId}/bookyears/{bookyearId}/journals` (24/dag) |
| `octopus_dagboeken` | Dagboeken van een boekjaar. | `GET /dossiers/{dossierId}/bookyears/{bookyearId}/journals` (24/dag) |
| `octopus_dagboek_detail` | Detail van één dagboek per type A/V/F/D/L. | `GET /dossiers/{dossierId}/bookyears/{bookyearId}/journals/A/{sequenceNumber}` (24/dag) |
| `octopus_dagboeksaldo` | Saldo van een (financieel) dagboek. | `GET /dossiers/{dossierId}/bookyears/{bookyearId}/journals/{journalKey}` (24/dag) |
| `octopus_dagboeken_gewijzigd` | Dagboeken gewijzigd sinds een tijdstip. | `GET /dossiers/{dossierId}/journals/modified` (48/dag) |

### Boekhouding via lokale synchronisatie (eerst cache)

| Tool | Wat het doet | Octopus-endpoint (daglimiet) |
|---|---|---|
| `octopus_sync` | Haalt rekeningen, saldi, relaties en boekingen op en houdt ze lokaal bij via de gewijzigd-sinds-endpoints (eerste keer volledig, daarna alleen wijzigingen). Versleuteld op schijf met OCTOPUS_CACHE_KEY, anders alleen in het geheugen. | lokaal |
| `octopus_rekeningschema` | Grootboekrekeningen van een boekjaar via lokale synchronisatie. | `GET /dossiers/{dossierId}/accounts` (2/dag)<br>`GET /dossiers/{dossierId}/accounts/modified` (48/dag) |
| `octopus_rekeningsaldi` | Saldi per rekening per periode via synchronisatie. | `GET /dossiers/{dossierId}/accounts/amounts/modified` (48/dag) |
| `octopus_proefbalans` | Proefbalans samengesteld uit rekeningen en saldi per periode (Octopus heeft geen proefbalans-endpoint). Saldo = debet - credit; controle op evenwicht en per klasse (MAR). | lokaal |
| `octopus_boekingslijnen` | Boekingslijnen van een boekjaar via synchronisatie (eerste keer 4 calls per boekjaar, daarna 1; GET /dossiers/{dossierId}/bookyears/{bookyearId}/bookings/modified; daglimiet 48). | `GET /dossiers/{dossierId}/bookyears/{bookyearId}/bookings/modified` (48/dag) |
| `octopus_relaties` | Klanten en leveranciers. Zonder zoekterm via synchronisatie. | `GET /dossiers/{dossierId}/relations` (2/dag)<br>`GET /dossiers/{dossierId}/relations/modified` (48/dag)<br>`GET /dossiers/{dossierId}/relations` (400/dag) |

### Rapporten, openstaande posten en analyses

| Tool | Wat het doet | Octopus-endpoint (daglimiet) |
|---|---|---|
| `octopus_openstaande_posten` | Openstaande posten van klanten (debiteuren), leveranciers (crediteuren) of één rekening. | `POST /dossiers/{dossierId}/reports/clients/open` (24/dag) |
| `octopus_ouderdom_openstaande_posten` | Ouderdomsanalyse (niet vervallen, 0-30, 31-60, 61-90, >90 dagen, zonder datum, negatief). | `POST /dossiers/{dossierId}/reports/clients/open` (24/dag) |
| `octopus_historiek` | Historiekrapport per rekening, klant, leverancier of kostenplaats over een boekjaar- en periodebereik. | `POST /dossiers/{dossierId}/reports/accounts/history` (24/dag) |
| `octopus_dashboard_kpis` | Kerncijfers uit de samengestelde proefbalans (omzet, kosten, resultaat, liquide middelen, btw-indicatie) plus open debiteuren/crediteuren. Indeling volgens het Belgische MAR. | lokaal |

### Boekingen en documenten (lezen)

| Tool | Wat het doet | Octopus-endpoint (daglimiet) |
|---|---|---|
| `octopus_boekingen_gewijzigd` | Ruwe sync-call: boekingslijnen gewijzigd sinds een tijdstip. Eerste keer per boekjaar en dagboektype 1-4; daarna boekjaar -1 en type -1. Gebruik bij voorkeur octopus_sync of octopus_boekingslijnen. | `GET /dossiers/{dossierId}/bookyears/{bookyearId}/bookings/modified` (48/dag) |
| `octopus_aankoop_verkoop_boeking` | Eén aankoop- of verkoopdocument met lijnen. | `GET /dossiers/{dossierId}/buysellbookings` (10/dag) |
| `octopus_aankoop_verkoop_gewijzigd` | Aankoop/verkoop-documenten gewijzigd sinds een tijdstip. | `GET /dossiers/{dossierId}/buysellbookings/modified` (48/dag) |
| `octopus_financieel_divers_boeking` | Eén financieel of divers document met lijnen. | `GET /dossiers/{dossierId}/financialdiversbookings` (10/dag) |
| `octopus_financieel_divers_gewijzigd` | Financiële/diverse documenten gewijzigd sinds een tijdstip. | `GET /dossiers/{dossierId}/financialdiversbookings/modified` (48/dag) |
| `octopus_onafgepunte_facturen` | Facturen die nog niet afgepunt zijn. | `GET /dossiers/{dossierId}/bank/invoices` (48/dag) |
| `octopus_afpuntingen_gewijzigd` | Afpuntingen gewijzigd sinds een tijdstip. | `GET /dossiers/{dossierId}/balancings/modified` (48/dag) |
| `octopus_betaallijst` | Inhoud van de betaallijst (alleen lezen). | `GET /dossiers/{dossierId}/bank/paymentlist` (48/dag) |
| `octopus_enveloppes` | Betalingsenveloppes of de inhoud van één enveloppe (alleen lezen; GET /dossiers/{dossierId}/bank/enveloppes; daglimiet 48). | `GET /dossiers/{dossierId}/bank/enveloppes` (48/dag) |
| `octopus_facturen_gewijzigd` | Facturen uit de factuurmodule, gewijzigd sinds een tijdstip (module moet actief zijn). | `GET /dossiers/{dossierId}/invoices/modified` (48/dag) |
| `octopus_factuur` | Eén factuur uit de factuurmodule. | `GET /dossiers/{dossierId}/invoices` (400/dag) |
| `octopus_leveringsbonnen_gewijzigd` | Leveringsbonnen gewijzigd sinds een tijdstip. | `GET /dossiers/{dossierId}/deliverynotes/modified` (48/dag) |
| `octopus_rappels` | Rappelinformatie tot een vervaldatum. | `GET /dossiers/{dossierId}/rappels` (400/dag) |

### Stamdata (2 calls per dag: 12 uur gecachet)

| Tool | Wat het doet | Octopus-endpoint (daglimiet) |
|---|---|---|
| `octopus_btw_codes` | Btw-codes van het dossier (stamdata: 2 calls per dag, 12 uur gecachet). | `GET /dossiers/{dossierId}/vatcodes` (2/dag) |
| `octopus_munten` | Muntcodes van het dossier (stamdata). | `GET /dossiers/{dossierId}/currencies` (2/dag) |
| `octopus_vrije_velden` | Vrije velden (custom fields) van het dossier (stamdata). | `GET /dossiers/{dossierId}/customfields` (2/dag) |
| `octopus_producten` | Producten (stamdata). | `GET /dossiers/{dossierId}/products` (2/dag) |
| `octopus_productgroepen` | Productgroepen (stamdata). | `GET /dossiers/{dossierId}/productgroups` (2/dag) |
| `octopus_kostenplaatsen` | Kostenplaatsen, optioneel alleen actieve. | `GET /dossiers/{dossierId}/costcentres` (2/dag) |

### Export en dossieroverdracht

| Tool | Wat het doet | Octopus-endpoint (daglimiet) |
|---|---|---|
| `octopus_export_dataset` | Schrijft een dataset (kpis, saldi, proefbalans, openstaande_posten, boekingslijnen, rekeningschema, relaties) naar CSV, JSON, Excel of Parquet in een lokale map. Schrijft nooit naar Octopus. | lokaal |
| `octopus_dossier_transfer_schatting` | Schat het aantal calls per endpoint voor een overdracht per boekjaar en vergelijkt met de resterende daglimieten. | lokaal |
| `octopus_dossier_transfer_export` | Volledig overdrachtspakket per boekjaar voor de volgende boekhouder: rekeningschema, proefbalans, boekingslijnen, openstaande posten, relaties, btw-codes, dagboeken, CONTROL.md, MANIFEST.json (SHA-256) en README. Alleen lezen; hervatbaar. | lokaal |

### Gratis officiële hulpdiensten en foutcodes

| Tool | Wat het doet | Octopus-endpoint (daglimiet) |
|---|---|---|
| `octopus_btw_nummer_controle` | Offline controle van een Belgisch btw-nummer (modulo 97) en optioneel een VIES-check bij de Europese Commissie (gratis, geen sleutel; alleen het nummer wordt verstuurd). | lokaal |
| `octopus_wisselkoers_ecb` | Euro-referentiekoers van de ECB voor een munt (gratis, ter informatie). | lokaal |
| `octopus_foutcode_uitleg` | Vraagt het voorbeeld-foutobject voor een Octopus-foutcode op. | `GET /error` (100/dag) |

### Schrijven (standaard UIT; OCTOPUS_WRITE_ENABLED=true, twee stappen)

| Tool | Wat het doet | Octopus-endpoint (daglimiet) |
|---|---|---|
| `octopus_schrijf_voorstel` | Bereidt een schrijfactie voor en toont exact wat er verstuurd zou worden. Verstuurt niets. | lokaal |
| `octopus_schrijf_bevestigen` | Verstuurt een eerder voorstel naar Octopus met de bevestigingscode. | lokaal |


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

Powered by FISCALCI Accounting & Tax (Askin Alci)
