"""Deterministic synthetic SAP S/4HANA ERP demo data and product normalization.

The generated records model a synthetic SAP S/4HANA enterprise landscape:
- Business Partners (BUT000)
- Sales Orders (VBAK/VBAP)
- Universal Journal Financial Postings (ACDOCA)
- Billing Documents (VBRK/VBRP)

The records exercise the semantic rules: multiple sales orders, qualifying and
excluded financial postings, three company codes/jurisdictions (FR, GB, DE),
and intentional raw quality failures for validation testing.
"""

from __future__ import annotations

import csv
from collections.abc import Iterable, Mapping
from datetime import date, timedelta
from pathlib import Path

import yaml

_CANONICAL_AUTOMOTIVE = "ciferp:ProductAutomotive"
_CANONICAL_COMMERCIAL = "ciferp:ProductCommercial"
_GOVERNED_PRODUCT_CONCEPTS = {_CANONICAL_AUTOMOTIVE, _CANONICAL_COMMERCIAL}
_PLATFORM_DIRECTORIES = {
    "databricks": "databricks/france.yaml",
    "snowflake": "snowflake/united_kingdom.yaml",
    "fabric": "fabric/germany.yaml",
    "microsoft fabric": "fabric/germany.yaml",
}


def canonical_product(platform: str, value: str) -> str:
    """Normalize a local ERP product/material code to a synthetic SAP-inspired concept.

    Unknown platforms and values fail closed rather than silently passing an
    unmapped local code into a semantic query.
    """
    platform_key = platform.strip().casefold()
    value_key = value.strip().casefold()
    relative_path = _PLATFORM_DIRECTORIES.get(platform_key)
    if relative_path is None:
        raise ValueError(f"unsupported mapping platform: {platform}")

    mapping_path = Path(__file__).resolve().parents[2] / "mappings" / relative_path
    try:
        document = yaml.safe_load(mapping_path.read_text())
    except FileNotFoundError as error:
        raise ValueError(f"mapping asset not found for platform: {platform}") from error

    products = document.get("normalization", {}).get("products", {})
    for local_value, canonical_value in products.items():
        if str(local_value).strip().casefold() == value_key:
            canonical = str(canonical_value)
            if canonical not in _GOVERNED_PRODUCT_CONCEPTS:
                raise ValueError(f"unregistered governed product {canonical!r}")
            return canonical
    raise ValueError(f"unmapped product {value!r} for platform {platform!r}")


def _write_csv(path: Path, fieldnames: list[str], rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _records(as_of: date) -> dict[str, list[dict[str, object]]]:
    """Return stable records anchored to ``as_of`` rather than wall-clock time."""

    def d(days: int) -> str:
        return (as_of - timedelta(days=days)).isoformat()

    future = (as_of + timedelta(days=1)).isoformat()

    business_partners = [
        {"partner_id": "FR_001", "partner_name": "Camille Martin", "country": "FR", "email": "camille.martin@example.test"},
        {"partner_id": "FR_002", "partner_name": "Julien Bernard", "country": "FR", "email": "julien.bernard@example.test"},
        {"partner_id": "FR_003", "partner_name": "Aline Petit", "country": "FR", "email": "aline.petit@example.test"},
        {"partner_id": "UK_001", "partner_name": "Oliver Smith", "country": "GB", "email": "oliver.smith@example.test"},
        {"partner_id": "DE_001", "partner_name": "Anna Schmidt", "country": "DE", "email": "anna.schmidt@example.test"},
    ]
    sales_orders = [
        {"sales_order_id": "FR_SO_001", "partner_id": "FR_001", "country": "FR", "product": _CANONICAL_AUTOMOTIVE, "order_status": "RELEASED", "effective_date": d(720), "expiry_date": d(-10), "net_value_eur": "1350.00"},
        {"sales_order_id": "FR_SO_002", "partner_id": "FR_001", "country": "FR", "product": _CANONICAL_AUTOMOTIVE, "order_status": "CLOSED", "effective_date": d(900), "expiry_date": d(400), "net_value_eur": "850.00"},
        {"sales_order_id": "FR_SO_003", "partner_id": "FR_002", "country": "FR", "product": _CANONICAL_AUTOMOTIVE, "order_status": "RELEASED", "effective_date": d(500), "expiry_date": d(-40), "net_value_eur": "1490.00"},
        {"sales_order_id": "UK_SO_001", "partner_id": "UK_001", "country": "GB", "product": _CANONICAL_AUTOMOTIVE, "order_status": "RELEASED", "effective_date": d(650), "expiry_date": d(-20), "net_value_eur": "1120.00"},
        {"sales_order_id": "DE_SO_001", "partner_id": "DE_001", "country": "DE", "product": _CANONICAL_AUTOMOTIVE, "order_status": "RELEASED", "effective_date": d(600), "expiry_date": d(-30), "net_value_eur": "980.00"},
    ]
    acdoca_financials = [
        {"journal_entry_id": "FR_DOC_001", "sales_order_id": "FR_SO_001", "partner_id": "FR_001", "country": "FR", "product": _CANONICAL_AUTOMOTIVE, "posting_status": "POSTED", "posting_date": d(30), "amount_in_company_currency_eur": "9000.00"},
        {"journal_entry_id": "FR_DOC_002", "sales_order_id": "FR_SO_001", "partner_id": "FR_001", "country": "FR", "product": _CANONICAL_AUTOMOTIVE, "posting_status": "CLEARED", "posting_date": d(120), "amount_in_company_currency_eur": "8000.00"},
        {"journal_entry_id": "FR_DOC_003", "sales_order_id": "FR_SO_001", "partner_id": "FR_001", "country": "FR", "product": _CANONICAL_AUTOMOTIVE, "posting_status": "POSTED", "posting_date": d(200), "amount_in_company_currency_eur": "7000.00"},
        {"journal_entry_id": "FR_DOC_004", "sales_order_id": "FR_SO_001", "partner_id": "FR_001", "country": "FR", "product": _CANONICAL_AUTOMOTIVE, "posting_status": "REVERSED", "posting_date": d(45), "amount_in_company_currency_eur": "50000.00"},
        {"journal_entry_id": "FR_DOC_005", "sales_order_id": "FR_SO_001", "partner_id": "FR_001", "country": "FR", "product": _CANONICAL_AUTOMOTIVE, "posting_status": "DUPLICATE", "posting_date": d(46), "amount_in_company_currency_eur": "50000.00"},
        {"journal_entry_id": "FR_DOC_006", "sales_order_id": "FR_SO_001", "partner_id": "FR_001", "country": "FR", "product": _CANONICAL_AUTOMOTIVE, "posting_status": "CLEARED", "posting_date": d(400), "amount_in_company_currency_eur": "12000.00"},
        {"journal_entry_id": "FR_DOC_007", "sales_order_id": "FR_SO_003", "partner_id": "FR_002", "country": "FR", "product": _CANONICAL_AUTOMOTIVE, "posting_status": "POSTED", "posting_date": d(60), "amount_in_company_currency_eur": "12000.00"},
        {"journal_entry_id": "FR_DOC_008", "sales_order_id": "FR_SO_003", "partner_id": "FR_002", "country": "FR", "product": _CANONICAL_AUTOMOTIVE, "posting_status": "POSTED", "posting_date": d(160), "amount_in_company_currency_eur": "11000.00"},
        {"journal_entry_id": "FR_DOC_009", "sales_order_id": "FR_SO_003", "partner_id": "FR_002", "country": "FR", "product": _CANONICAL_AUTOMOTIVE, "posting_status": "CLEARED", "posting_date": d(240), "amount_in_company_currency_eur": "2000.00"},
        {"journal_entry_id": "UK_DOC_001", "sales_order_id": "UK_SO_001", "partner_id": "UK_001", "country": "GB", "product": _CANONICAL_AUTOMOTIVE, "posting_status": "POSTED", "posting_date": d(75), "amount_in_company_currency_eur": "4200.00"},
        {"journal_entry_id": "DE_DOC_001", "sales_order_id": "DE_SO_001", "partner_id": "DE_001", "country": "DE", "product": _CANONICAL_AUTOMOTIVE, "posting_status": "CLEARED", "posting_date": d(180), "amount_in_company_currency_eur": "7600.00"},
        {"journal_entry_id": "DE_DOC_002", "sales_order_id": "DE_SO_001", "partner_id": "DE_001", "country": "DE", "product": _CANONICAL_AUTOMOTIVE, "posting_status": "REVERSED", "posting_date": d(190), "amount_in_company_currency_eur": "1800.00"},
    ]
    billing_documents = [
        {"billing_doc_id": "FR_BIL_001", "sales_order_id": "FR_SO_001", "partner_id": "FR_001", "country": "FR", "product": _CANONICAL_AUTOMOTIVE, "billing_date": d(20), "billed_amount_eur": "1350.00"},
        {"billing_doc_id": "FR_BIL_002", "sales_order_id": "FR_SO_003", "partner_id": "FR_002", "country": "FR", "product": _CANONICAL_AUTOMOTIVE, "billing_date": d(20), "billed_amount_eur": "1490.00"},
        {"billing_doc_id": "UK_BIL_001", "sales_order_id": "UK_SO_001", "partner_id": "UK_001", "country": "GB", "product": _CANONICAL_AUTOMOTIVE, "billing_date": d(20), "billed_amount_eur": "1120.00"},
        {"billing_doc_id": "DE_BIL_001", "sales_order_id": "DE_SO_001", "partner_id": "DE_001", "country": "DE", "product": _CANONICAL_AUTOMOTIVE, "billing_date": d(20), "billed_amount_eur": "980.00"},
    ]
    raw_business_partners = [*business_partners, {"partner_id": "", "partner_name": "Invalid Partner", "country": "FR", "email": "invalid@example.test"}]
    raw_sales_orders = [*sales_orders, {**sales_orders[0], "sales_order_id": "RAW_NEGATIVE", "net_value_eur": "-1.00"}]
    raw_acdoca_financials = [
        *acdoca_financials,
        {**acdoca_financials[0], "journal_entry_id": "RAW_FUTURE", "posting_date": future},
        {**acdoca_financials[0], "journal_entry_id": "RAW_NEGATIVE", "amount_in_company_currency_eur": "-10.00"},
        {**acdoca_financials[0], "journal_entry_id": "RAW_STATUS", "posting_status": "UNKNOWN"},
        {**acdoca_financials[0], "journal_entry_id": "FR_DOC_001", "posting_date": d(31)},
    ]
    raw_billing_documents = [*billing_documents, {**billing_documents[0], "billing_doc_id": "RAW_NEGATIVE", "billed_amount_eur": "-25.00"}]
    return {
        "business_partners": business_partners,
        "sales_orders": sales_orders,
        "acdoca_financials": acdoca_financials,
        "billing_documents": billing_documents,
        "raw_business_partners": raw_business_partners,
        "raw_sales_orders": raw_sales_orders,
        "raw_acdoca_financials": raw_acdoca_financials,
        "raw_billing_documents": raw_billing_documents,
    }


def generate_demo_data(output_dir: Path, as_of: date) -> None:
    """Write deterministic curated and intentionally imperfect raw CSVs."""
    records = _records(as_of)
    columns = {
        "business_partners": ["partner_id", "partner_name", "country", "email"],
        "sales_orders": ["sales_order_id", "partner_id", "country", "product", "order_status", "effective_date", "expiry_date", "net_value_eur"],
        "acdoca_financials": ["journal_entry_id", "sales_order_id", "partner_id", "country", "product", "posting_status", "posting_date", "amount_in_company_currency_eur"],
        "billing_documents": ["billing_doc_id", "sales_order_id", "partner_id", "country", "product", "billing_date", "billed_amount_eur"],
    }
    destination = Path(output_dir)
    for name, fieldnames in columns.items():
        _write_csv(destination / "curated" / f"{name}.csv", fieldnames, records[name])
        _write_csv(destination / "raw" / f"{name}.csv", fieldnames, records[f"raw_{name}"])


__all__ = ["canonical_product", "generate_demo_data"]
