# Postman-collectie

> Bedoeld voor Belgische boekhouders/accountants; gebaseerd op Belgische boekhoud- en btw-regels (MAR, Belgisch btw-stelsel). Gebruik buiten België: verifieer zelf de lokale regels.
>
> Powered by FISCALCI Accounting & Tax (Askin Alci)

`postman/FISCAi-Octopus-API-Connector.postman_collection.json` wordt gegenereerd door `scripts/build_postman.py` uit de officiële specificatie van de Octopus REST API (service.inaras.be). Ze bevat **alleen de 50 leesoperaties** in 21 mappen, plus twee aanmeldverzoeken. English: [POSTMAN.md](POSTMAN.md).

1. Importeer de collectie en `postman/FISCAi-Octopus-API-Connector.postman_environment.json`.
2. Vul `softwareHouseUuid`, `user` en `password` in **uw eigen** omgeving in als *secret* (nooit in de collectie, nooit delen of synchroniseren met een teamwerkruimte).
3. Voer **0. Aanmelden** en **1. Dossiertoken** uit (elk 10 minuten geldig); testscripts bewaren de tokens. Herhaal na 10 minuten.
4. Vul `dossierId`, `bookyearId` en `modifiedTimeStamp` (formaat `2026-01-01 00:00:00.000`).

**Let op de daglimieten**: elk verzoek telt mee voor de daglimieten van Octopus **en wordt niet geteld door het quotabestand van de connector**. Sommige endpoints laten maar 2 calls per dag toe. Test bij voorkeur op het demodossier. Schrijfoperaties zijn bewust niet opgenomen.
