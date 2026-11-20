---
name: fiscai-octopus-api-connector
description: Use when you need Octopus accounting figures (dossiers, bookyears, trial balance, open customer and supplier items, aging, KPIs, exports, dossier transfer) through the FISCAi Octopus API Connector plugin; read-only and with very low daily limits per endpoint. Gebruik voor Octopus-cijfers, proefbalans, openstaande posten en dossieroverdracht.
---

# FISCAi Octopus API Connector

Powered by FISCALCI Accounting & Tax (Askin Alci)

Bedoeld voor Belgische boekhouders/accountants; gebaseerd op Belgische boekhoud- en btw-regels (MAR, Belgisch btw-stelsel). Gebruik buiten België: verifieer zelf de lokale regels.

## Wanneer gebruiken
Voor elke vraag die Octopus-gegevens nodig heeft: dossiers en boekjaren, rekeningschema, proefbalans, boekingslijnen, openstaande posten en ouderdom, KPI's, exports of een dossieroverdracht per boekjaar.

## Harde regels
- **Schrijven staat UIT.** Zonder `OCTOPUS_WRITE_ENABLED=true` bestaan er geen schrijftools. Zet die variabele nooit zelf. Staat ze aan: altijd eerst `octopus_schrijf_voorstel` tonen en pas na een uitdrukkelijk "ja" `octopus_schrijf_bevestigen`; één actie per bevestiging.
- **Daglimieten per endpoint zijn zeer laag** (rekeningen, btw-codes, relaties zonder zoekterm: 2 per dag; aankoop/verkoop- en financieel/diverse boekingen: 10; gewijzigde-endpoints: 48). Kijk eerst `octopus_quota`, synchroniseer met `octopus_sync` en werk daarna met de lokale tools. `vers: true` kost een call: alleen op vraag.
- Bereikt een endpoint zijn limiet, dan weigert de connector vóór het versturen. Probeer niet opnieuw; meld het resettijdstip.
- Nooit de Octopus Management API of een betalend plan. VIES en ECB zijn optionele gratis hulpdiensten.
- Vraag of herhaal nooit wachtwoord of software house UUID.

## Proefbalans en saldi
- Octopus heeft geen proefbalans-endpoint: `octopus_proefbalans` stelt ze samen uit rekeningen en saldi per periode. Saldo = debet min credit; opbrengsten zijn dus negatief.
- De betekenis van de periodesaldi (`OCTOPUS_AMOUNTS_MODE`: beweging of cumulatief) en de tekenconventie: verifieer actuele regel op het demodossier (zie `docs/OPEN-QUESTIONS.md`).
- Een negatief openstaand bedrag is na te gaan (creditnota, niet afgepunte betaling, voorschot, te veel betaald), geen conclusie.

## Vertrouwelijkheid
Boekhoudgegevens zijn vertrouwelijk. Toon alleen wat nodig is, gebruik [Voorbeeld] als placeholder en schrijf exports alleen naar een map die de gebruiker opgeeft. Workflowmails zijn concepten (`.eml`); de gebruiker verstuurt zelf.

## Dossieroverdracht
Eerst `octopus_dossier_transfer_schatting` (calls per endpoint tegenover de daglimiet), dan `octopus_dossier_transfer_export` met `bevestig: true`. Een onderbroken export hervat later via het checkpoint. Deontologie, GDPR en bewaartermijnen: verifieer actuele regel (`docs/DOSSIER-TRANSFER.nl.md`).

## Voorbeeld
"Geef de ouderdomsanalyse van de klanten van dossier [Voorbeeld] per 30/11/2026": `octopus_quota`, daarna `octopus_ouderdom_openstaande_posten` met `dossier_id`, `soort: "debiteuren"`, `peildatum: "2026-11-30"`; vermeld de `bron` en dat de cijfers door de boekhouder na te kijken zijn.
