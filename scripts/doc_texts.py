"""Tooldocumentatie: groepen en Engelse omschrijvingen (Nederlandse komen uit de tooldefinities zelf)."""

GROUPS = [
    ("local", "Status and daily limits (no Octopus call)", "Status en daglimieten (geen Octopus-call)", [
        "octopus_status", "octopus_quota", "octopus_sync_status", "octopus_export_schema"]),
    ("basics", "Session, dossiers and fiscal years", "Sessie, dossiers en boekjaren", [
        "octopus_api_versie", "octopus_whoami", "octopus_dossiers", "octopus_boekjaren", "octopus_boekjaar_detail", "octopus_boekjaar_status",
        "octopus_dagboeken", "octopus_dagboek_detail", "octopus_dagboeksaldo", "octopus_dagboeken_gewijzigd"]),
    ("ledger", "Ledger via local sync (cache-first)", "Boekhouding via lokale synchronisatie (eerst cache)", [
        "octopus_sync", "octopus_rekeningschema", "octopus_rekeningsaldi", "octopus_proefbalans", "octopus_boekingslijnen", "octopus_relaties"]),
    ("reports", "Reports, open items and analyses", "Rapporten, openstaande posten en analyses", [
        "octopus_openstaande_posten", "octopus_ouderdom_openstaande_posten", "octopus_historiek", "octopus_dashboard_kpis"]),
    ("docs", "Bookings and documents (read)", "Boekingen en documenten (lezen)", [
        "octopus_boekingen_gewijzigd", "octopus_aankoop_verkoop_boeking", "octopus_aankoop_verkoop_gewijzigd", "octopus_financieel_divers_boeking",
        "octopus_financieel_divers_gewijzigd", "octopus_onafgepunte_facturen", "octopus_afpuntingen_gewijzigd", "octopus_betaallijst", "octopus_enveloppes",
        "octopus_facturen_gewijzigd", "octopus_factuur", "octopus_leveringsbonnen_gewijzigd", "octopus_rappels"]),
    ("master", "Master data (2 calls per day: cached 12 h)", "Stamdata (2 calls per dag: 12 uur gecachet)", [
        "octopus_btw_codes", "octopus_munten", "octopus_vrije_velden", "octopus_producten", "octopus_productgroepen", "octopus_kostenplaatsen"]),
    ("export", "Export and dossier transfer", "Export en dossieroverdracht", [
        "octopus_export_dataset", "octopus_dossier_transfer_schatting", "octopus_dossier_transfer_export"]),
    ("helpers", "Free official helpers and error codes", "Gratis officiële hulpdiensten en foutcodes", [
        "octopus_btw_nummer_controle", "octopus_wisselkoers_ecb", "octopus_foutcode_uitleg"]),
    ("write", "Write (OFF by default; OCTOPUS_WRITE_ENABLED=true, two steps)", "Schrijven (standaard UIT; OCTOPUS_WRITE_ENABLED=true, twee stappen)", [
        "octopus_schrijf_voorstel", "octopus_schrijf_bevestigen"]),
]

EN = {
    "octopus_status": "Configuration (without secrets), daily limits, cache and version. Makes no Octopus call.",
    "octopus_quota": "Used and remaining calls per Octopus endpoint today (Europe/Brussels). Makes no call.",
    "octopus_sync_status": "Watermarks and record counts of the local sync. Makes no call.",
    "octopus_export_schema": "Columns and types of the export datasets (Power BI, Excel, databases). Makes no call.",
    "octopus_api_versie": "Version of the Octopus REST API.",
    "octopus_whoami": "Information about the signed-in Octopus user.",
    "octopus_dossiers": "Dossiers the user can access (respects OCTOPUS_ALLOWED_DOSSIERS).",
    "octopus_boekjaren": "Fiscal years with their periods.",
    "octopus_boekjaar_detail": "Details of one fiscal year.",
    "octopus_boekjaar_status": "Fiscal year status: closed or open, journals, protected/closed periods and sync state.",
    "octopus_dagboeken": "Journals of a fiscal year.",
    "octopus_dagboek_detail": "Detail of one journal by type (A/V/F/D/L).",
    "octopus_dagboeksaldo": "Balance of a (financial) journal.",
    "octopus_dagboeken_gewijzigd": "Journals modified since a timestamp.",
    "octopus_sync": "Fetches accounts, balances, relations and bookings and keeps them locally via the modified-since endpoints (full load once, then changes only).",
    "octopus_rekeningschema": "Chart of accounts of a fiscal year, from the local sync.",
    "octopus_rekeningsaldi": "Balances per account per period, from the local sync.",
    "octopus_proefbalans": "Trial balance built from accounts and balances per period (Octopus has no trial-balance endpoint); balance check and totals per MAR class.",
    "octopus_boekingslijnen": "Booking lines of a fiscal year, from the local sync (first time 4 calls per year, then 1).",
    "octopus_relaties": "Customers and suppliers; without a search term from the sync, with a search term directly (400/day).",
    "octopus_openstaande_posten": "Open items of customers (receivables), suppliers (payables) or one account.",
    "octopus_ouderdom_openstaande_posten": "Ageing of open items (not due, 0-30, 31-60, 61-90, over 90 days, no date, negative).",
    "octopus_historiek": "History report per account, customer, supplier or cost centre over a fiscal-year and period range.",
    "octopus_dashboard_kpis": "Key figures from the built trial balance (revenue, costs, result, cash, VAT indication) plus open receivables/payables (Belgian MAR).",
    "octopus_boekingen_gewijzigd": "Raw sync call: booking lines modified since a timestamp. Prefer octopus_sync.",
    "octopus_aankoop_verkoop_boeking": "One purchase or sales document with its lines (10/day).",
    "octopus_aankoop_verkoop_gewijzigd": "Purchase/sales documents modified since a timestamp.",
    "octopus_financieel_divers_boeking": "One financial or miscellaneous document with its lines (10/day).",
    "octopus_financieel_divers_gewijzigd": "Financial/miscellaneous documents modified since a timestamp.",
    "octopus_onafgepunte_facturen": "Invoices that are not yet matched (balanced).",
    "octopus_afpuntingen_gewijzigd": "Matchings (balancings) modified since a timestamp.",
    "octopus_betaallijst": "Contents of the payment list (read only).",
    "octopus_enveloppes": "Payment envelopes or the contents of one envelope (read only).",
    "octopus_facturen_gewijzigd": "Invoices from the invoicing module modified since a timestamp (module must be active).",
    "octopus_factuur": "One invoice from the invoicing module.",
    "octopus_leveringsbonnen_gewijzigd": "Delivery notes modified since a timestamp.",
    "octopus_rappels": "Reminder (dunning) information up to a due date.",
    "octopus_btw_codes": "VAT codes of the dossier (master data: 2 calls per day, cached 12 h).",
    "octopus_munten": "Currency codes of the dossier (master data).",
    "octopus_vrije_velden": "Custom fields of the dossier (master data).",
    "octopus_producten": "Products (master data).",
    "octopus_productgroepen": "Product groups (master data).",
    "octopus_kostenplaatsen": "Cost centres, optionally active only (master data).",
    "octopus_export_dataset": "Writes a dataset (kpis, balances, trial balance, open items, booking lines, chart of accounts, relations) to CSV, JSON, Excel or Parquet. Never writes to Octopus.",
    "octopus_dossier_transfer_schatting": "Estimates the calls per endpoint for a per-fiscal-year transfer and compares them with the remaining daily limits.",
    "octopus_dossier_transfer_export": "Complete per-fiscal-year package for the next accountant, with CONTROL.md, MANIFEST.json (SHA-256) and README. Read only; resumable.",
    "octopus_btw_nummer_controle": "Offline check of a Belgian VAT number (modulo 97), optionally a VIES check with the European Commission (free, no key).",
    "octopus_wisselkoers_ecb": "ECB euro reference rate for a currency (free, for information).",
    "octopus_foutcode_uitleg": "Fetches the sample error object for an Octopus error code (100/day).",
    "octopus_schrijf_voorstel": "Step 1: prepares a write action and shows exactly what would be sent, with a confirmation code. Sends nothing.",
    "octopus_schrijf_bevestigen": "Step 2: sends a prepared proposal to Octopus with its confirmation code (WRITES; daily maximum).",
}
