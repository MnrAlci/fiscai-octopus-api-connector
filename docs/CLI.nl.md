# Opdrachtregel: `octopus-api-connector`

> Bedoeld voor Belgische boekhouders/accountants; gebaseerd op Belgische boekhoud- en btw-regels (MAR, Belgisch btw-stelsel). Gebruik buiten België: verifieer zelf de lokale regels.
>
> Powered by FISCALCI Accounting & Tax (Askin Alci)

Geïnstalleerd als `octopus-api-connector` (`pip install .`), of zonder installatie: `python3 server/run_cli.py ...`. English: [CLI.md](CLI.md).

## Opdrachten

| Opdracht | Wat het doet | Octopus-calls |
|---|---|---|
| `serve` | Start de MCP-server over stdio. | per tool |
| `doctor` | Controleert Python, afhankelijkheden, configuratie, versleutelde cache, schrijfmodus en naamsvermelding. Toont nooit geheimen. | geen |
| `tools [--json]` | Lijst van alle tools. | geen |
| `call TOOL naam=waarde ...` | Voert één **alleen-lezen** tool uit. Waarden mogen JSON zijn. Schrijftools worden geweigerd (code 6). | per tool |
| `sync --dossier ID [--bookyear ID]` | Synchroniseert rekeningen, saldi, relaties en boekingen (eerst volledig, daarna alleen wijzigingen). | eerste keer 4-8, daarna 4 |
| `quota [--json]` | Gebruikte en resterende calls per endpoint vandaag. | geen |
| `export DATASET --dossier ID --out MAP ...` | Schrijft `kpis`, `saldi`, `proefbalans`, `openstaande_posten`, `boekingslijnen`, `rekeningschema` of `relaties`. | uit cache/sync |
| `transfer --dossier ID --out MAP [--bookyear ID ...] [--yes]` | Dossieroverdracht per boekjaar. Zonder `--yes` alleen de schatting per endpoint. Hervatbaar. | zie schatting |
| `workflows init\|list\|plan\|run` | Automatisering ([AUTOMATION.nl.md](AUTOMATION.nl.md)). | `plan`: geen |
| `cache status` / `cache clear --yes` | Toont of wist de lokale cache en synchronisatie (niet de dagteller). | geen |
| `config init` | Schrijft een voorbeeld-`.env` met alleen plaatshouders. | geen |
| `version`, `completion bash\|zsh\|powershell` | Versie; shell-aanvulling. | geen |

Gemeenschappelijke opties: `--json`, `-q`, `-v`, `--log-level`, `--log-format text|json`, `--env-file`, `--hooks`, `--dry-run`, `--data-dir`.

Afsluitcodes: 0 ok, 1 fout, 2 gebruik, 3 configuratie, 4 tool/Octopus, 5 netwerk, 6 geweigerd (daglimiet bereikt, schrijftool, dossier niet toegelaten, verzenden zonder toestemming).

```bash
octopus-api-connector doctor
octopus-api-connector sync --dossier 101 --bookyear 2
octopus-api-connector call octopus_proefbalans dossier_id=101 jaar=2026
octopus-api-connector transfer --dossier 101 --out ./overdracht --yes
```

Dossier 101 is een `[Voorbeeld]`-waarde.
