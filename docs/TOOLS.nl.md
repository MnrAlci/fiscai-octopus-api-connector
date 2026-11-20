# Tools

51 tools: **49 alleen-lezen/lokaal** (altijd aan) en **2 schrijftools** die alleen bestaan met `OCTOPUS_WRITE_ENABLED=true`.
De daglimieten komen uit de officiële Octopus REST-specificatie ("Maximum allowed calls per day"); de connector weigert een call *voor* hij verstuurd wordt als de limiet van vandaag (Europe/Brussels) bereikt is. Zie `octopus_quota`.

_Gegenereerd door `scripts/build_docs.py`. English: [TOOLS.md](TOOLS.md)._

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

Powered by FISCALCI Accounting & Tax (Askin Alci)
