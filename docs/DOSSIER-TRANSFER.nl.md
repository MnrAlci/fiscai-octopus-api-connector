# Dossieroverdracht per boekjaar

> Bedoeld voor Belgische boekhouders/accountants; gebaseerd op Belgische boekhoud- en btw-regels (MAR, Belgisch btw-stelsel). Gebruik buiten België: verifieer zelf de lokale regels.
>
> Powered by FISCALCI Accounting & Tax (Askin Alci)

Wanneer een klant naar een andere boekhouder overstapt, maakt `octopus_dossier_transfer_export` (MCP) of `octopus-api-connector transfer` (CLI) een pakket per boekjaar met **alleen-lezen** toegang tot Octopus. English: [DOSSIER-TRANSFER.md](DOSSIER-TRANSFER.md).

## Twee stappen
1. **Schatting** (`octopus_dossier_transfer_schatting` of `transfer` zonder `--yes`): aantal calls per endpoint tegenover de resterende daglimiet. Stamdata (rekeningen per boekjaar, relaties, btw-codes) mogen maar **2 keer per dag**; een overdracht van meerdere jaren kan dus meer dan één dag duren.
2. **Export** (`bevestig=true` / `--yes`): schrijft het pakket. Is een daglimiet bereikt, dan blijven de reeds geëxporteerde onderdelen bewaard in een checkpoint; voer dezelfde opdracht later (bv. morgen) opnieuw uit om te hervatten.

## Inhoud
| Pad | Inhoud |
|---|---|
| `dossier/relaties`, `btw-codes`, `kostenplaatsen`, `boekjaren` | Stamdata van het dossier |
| `boekjaar-<id>/boekjaar`, `dagboeken` | Boekjaar en dagboeken |
| `boekjaar-<id>/rekeningschema` | Rekeningschema zoals Octopus het geeft (MAR/PCMN; niet hernummerd) |
| `boekjaar-<id>/proefbalans-einde` | Proefbalans **samengesteld** uit saldi per rekening per periode (geen proefbalans-endpoint) |
| `boekjaar-<id>/boekingslijnen` | Alle boekingslijnen (weglaten met `--no-lines`) |
| `boekjaar-<id>/openstaande-klanten-einde`, `-leveranciers-einde` | Openstaande posten op het einde van het boekjaar |
| `CONTROL.md` | Afstemmingen: debet = credit, boekingen = saldi, open posten t.o.v. 40/44; afwijkingen als AFWIJKING |
| `MANIFEST.json` | Bestanden met rijen en SHA-256 |
| `README.md` | Uitleg voor de ontvangende boekhouder, met deontologische en GDPR-punten |

Formaten: csv, json, xlsx. Optioneel `--zip` (niet versleuteld: versleutel zelf vóór het overmaken).

## Beperkingen (verifieer actuele regel)
- De betekenis van periodesaldi (beweging of cumulatief, `OCTOPUS_AMOUNTS_MODE`) en de tekenconventie zijn te verifiëren op het demodossier.
- Geen activaregister, afschrijvingstabellen of bijlagen via de gebruikte endpoints.
- Volg de regels van uw beroepsinstituut voor de overdracht en het contact met de confrater; de klant blijft eigenaar van zijn gegevens. De connector verstuurt zelf niets.
