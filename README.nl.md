<p align="center">
  <img src="assets/logo.png" alt="FISCAi Octopus API Connector, plugin voor Grok Bot" width="220">
</p>

<h1 align="center">FISCAi Octopus API Connector <br><sub>Plugin voor Grok Bot, werkt ook in Copilot, Claude, Cursor, Windsurf en andere MCP-clients</sub></h1>

<p align="center"><b>Alleen-lezen toegang tot de Octopus-boekhoud-API (REST), gebouwd rond de zeer lage daglimieten: eerst cache, synchroniseren via de gewijzigd-sinds-endpoints, nooit een betalend plan.</b></p>

<p align="center"><a href="README.md">English</a> &middot; <a href="docs/TOOLS.nl.md">Tools</a> &middot; <a href="docs/manuals/handleiding.nl.md">Handleiding</a> &middot; <a href="CHANGELOG.md">Changelog</a></p>

Powered by FISCALCI Accounting & Tax (Askin Alci)

Auteur: Askin Alci

> Bedoeld voor Belgische boekhouders/accountants; gebaseerd op Belgische boekhoud- en btw-regels (MAR, Belgisch btw-stelsel). Gebruik buiten België: verifieer zelf de lokale regels.

## Over

FISCAi Octopus API Connector is een lokale MCP-server (stdio) en opdrachtregeltool waarmee Grok Bot en andere MCP-clients Octopus-dossiers lezen: boekjaren, dagboeken, rekeningschema, saldi per periode, boekingslijnen, klanten en leveranciers, openstaande posten en rapporten. Daarbovenop maakt hij wat de API niet rechtstreeks biedt (een **proefbalans**, ouderdomsanalyse, kerncijfers volgens het MAR) en levert hij exports en een **dossieroverdracht per boekjaar** voor de volgende boekhouder. Status: **0.1.0 (alfa)**, offline getest tegen een nagebootste API op basis van de officiële specificatie; nog niet gevalideerd op een echt Octopus-dossier (zie [open vragen](docs/OPEN-QUESTIONS.md)).

**Meer.** [Handleiding (NL)](docs/manuals/handleiding.nl.md) · [Manual (EN)](docs/manuals/manual.en.md) · [Opdrachtregel](docs/CLI.nl.md) · [Hooks](docs/HOOKS.nl.md) · [Automatisering](docs/AUTOMATION.nl.md) · [Dossieroverdracht](docs/DOSSIER-TRANSFER.nl.md) · [Exportschema](docs/EXPORT-SCHEMA.md) · [Integraties](docs/integrations/README.nl.md) · [Postman](docs/POSTMAN.nl.md) · [Schrijfmodus](docs/WRITE.md) · [Open vragen](docs/OPEN-QUESTIONS.md) · [Agents](AGENTS.md)

## Wat het doet

- **49 alleen-lezen tools** (51 met de optionele schrijfmodus): dossiers, boekjaren, dagboeken, rekeningschema, saldi, boekingslijnen, relaties, openstaande posten, historiek, facturen, leveringsbonnen, rappels, stamdata.
- **Proefbalans** samengesteld uit rekeningen en saldi per periode, omdat Octopus geen proefbalans-endpoint heeft; met evenwichtscontrole en totalen per MAR-klasse.
- **Analyses:** ouderdom van openstaande posten, kerncijfers (omzet, kosten, resultaat, liquide middelen, vorderingen, schulden, btw-indicatie), vergelijking met het vorige boekjaar.
- **Lokale synchronisatie** via de officiële gewijzigd-sinds-endpoints: één keer volledig, daarna alleen wijzigingen. Versleuteld op schijf met uw eigen sleutel, of alleen in het geheugen.
- **Export** naar CSV, JSON, Excel (xlsx) en Parquet.
- **Dossieroverdracht per boekjaar** met `CONTROL.md` en `MANIFEST.json` (SHA-256), hervatbaar wanneer een daglimiet bereikt is.
- **Automatisering:** vergaderingvoorbereiding en terugkerende verplichtingen als overzichten en conceptmails; standaard wordt niets verstuurd.
- **Gratis officiële hulpdiensten (optioneel):** controle van een Belgisch btw-nummer (offline modulo 97, optioneel VIES van de Europese Commissie) en ECB-referentiekoersen.

## Daglimieten

De officiële Octopus REST-specificatie legt **per endpoint een maximum aantal calls per dag** op, soms maar **2 per dag** (rekeningen, btw-codes, munten, kostenplaatsen, vrije velden, producten, productgroepen, relaties zonder zoekterm). De connector telt elke call **voor** hij verstuurd wordt en weigert wanneer de limiet van vandaag (Europe/Brussels) bereikt is, cachet volgens de limiet (12 uur voor stamdata), synchroniseert via de gewijzigd-sinds-endpoints zoals de specificatie beschrijft, vernieuwt de tokens van 10 minuten automatisch en gebruikt nooit de betalende Management API. Zie `octopus_quota`.

## Installatie en configuratie

Vereisten: Python 3.10+, `httpx`, `cryptography`. Toegang: een **software house UUID** van Octopus en een Octopus-gebruiker met API-rechten. Er is **geen sandbox**; test met het demodossier (verifieer actuele regel).

```bash
pip install -r requirements.txt
python server/run_cli.py config init          # .env met alleen plaatshouders
python server/run_cli.py doctor               # controle zonder calls
python server/run_cli.py sync --dossier 101 --bookyear 2
python server/run_cli.py call octopus_proefbalans dossier_id=101 jaar=2026
```

Variabelen: `OCTOPUS_SOFTWARE_HOUSE_UUID`, `OCTOPUS_USER`, `OCTOPUS_PASSWORD` (geheim, verplicht), `OCTOPUS_CACHE_KEY` (optioneel, minstens 16 tekens, versleutelt de lokale opslag), `OCTOPUS_LOCALE_ID`, `OCTOPUS_ALLOWED_DOSSIERS`, `OCTOPUS_QUOTA_RESERVE`, `OCTOPUS_AMOUNTS_MODE`, `OCTOPUS_WRITE_ENABLED` (standaard uit). Zie de [handleiding](docs/manuals/handleiding.nl.md).

## Veiligheid

Standaard alleen lezen; schrijven alleen met `OCTOPUS_WRITE_ENABLED=true`, in twee stappen met een bevestigingscode en een dagmaximum, nooit verwijderen. Geen centrale server; tokens alleen in het geheugen; geheimen worden uit elke uitvoer gefilterd; alleen de officiële host `service.inaras.be`. Geen fiscaal of juridisch advies.

## Licentie

Apache License 2.0, zie [LICENSE](LICENSE) en [NOTICE](NOTICE). De vermelding "Powered by FISCALCI Accounting & Tax (Askin Alci)" blijft ongewijzigd in elke kopie en in gegenereerde exports.

Octopus is een merk van de rechthebbende; dit project is er niet door goedgekeurd.

Powered by FISCALCI Accounting & Tax (Askin Alci)
