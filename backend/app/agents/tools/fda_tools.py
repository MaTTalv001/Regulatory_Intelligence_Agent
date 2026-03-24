"""FDA openFDA API tools for the Strands regulatory agent."""

import httpx
from strands import tool

from app.config import settings
from app.agents.event_stream import tool_start, tool_end

BASE = settings.openfda_base_url
_TIMEOUT = 30.0


def _params(search: str, limit: int) -> dict:
    params: dict = {"search": search, "limit": limit}
    if settings.openfda_api_key:
        params["api_key"] = settings.openfda_api_key
    return params


@tool
def search_fda_adverse_events(
    drug_name: str,
    limit: int = 10,
) -> dict:
    """Search FDA FAERS adverse event reports for a given drug.

    Args:
        drug_name: Brand name or substance name of the drug.
        limit: Maximum number of results (default 10, max 100).

    Returns:
        Adverse event reports including reactions, outcomes, and seriousness.
    """
    tool_start("search_fda_adverse_events", {"drug_name": drug_name})
    url = f"{BASE}/event.json"
    params = _params(
        search=f"patient.drug.medicinalproduct:{drug_name}",
        limit=min(limit, 100),
    )
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    results = data.get("results", [])
    total = data.get("meta", {}).get("results", {}).get("total", 0)
    summaries = []
    for r in results:
        patient = r.get("patient", {})
        reactions = [
            rx.get("reactionmeddrapt", "")
            for rx in patient.get("reaction", [])
        ]
        drugs = [
            d.get("medicinalproduct", "")
            for d in patient.get("drug", [])
        ]
        summaries.append({
            "safety_report_id": r.get("safetyreportid"),
            "serious": r.get("serious"),
            "country": r.get("primarysourcecountry"),
            "reactions": reactions,
            "concomitant_drugs": drugs,
            "patient_sex": patient.get("patientsex"),
        })
    tool_end("search_fda_adverse_events")
    return {"total_reports": total, "results": summaries}


@tool
def count_fda_adverse_event_reactions(
    drug_name: str,
    limit: int = 20,
) -> dict:
    """Count the most frequently reported adverse reactions for a drug in FAERS.

    Args:
        drug_name: Brand name or substance name of the drug.
        limit: Number of top reactions to return (default 20).

    Returns:
        Ranked list of adverse reactions with counts.
    """
    tool_start("count_fda_adverse_event_reactions", {"drug_name": drug_name})
    url = f"{BASE}/event.json"
    params: dict = {
        "search": f"patient.drug.medicinalproduct:{drug_name}",
        "count": "patient.reaction.reactionmeddrapt.exact",
        "limit": min(limit, 100),
    }
    if settings.openfda_api_key:
        params["api_key"] = settings.openfda_api_key
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    tool_end("count_fda_adverse_event_reactions")
    return {"reactions": data.get("results", [])}


@tool
def search_fda_drug_labels(
    drug_name: str,
    limit: int = 3,
) -> dict:
    """Search FDA drug labels (package inserts) for a given drug.

    Args:
        drug_name: Brand name or substance name.
        limit: Maximum number of labels to return.

    Returns:
        Drug label information including indications, warnings, and dosage.
    """
    tool_start("search_fda_drug_labels", {"drug_name": drug_name})
    url = f"{BASE}/label.json"
    params = _params(
        search=f'openfda.brand_name:"{drug_name}"',
        limit=min(limit, 10),
    )
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    results = data.get("results", [])
    labels = []
    for r in results:
        openfda = r.get("openfda", {})
        labels.append({
            "brand_name": openfda.get("brand_name", []),
            "generic_name": openfda.get("generic_name", []),
            "manufacturer": openfda.get("manufacturer_name", []),
            "application_number": openfda.get("application_number", []),
            "route": openfda.get("route", []),
            "indications_and_usage": (r.get("indications_and_usage") or [""])[0][:1000],
            "warnings": (r.get("warnings") or [""])[0][:1000],
            "dosage_and_administration": (r.get("dosage_and_administration") or [""])[0][:1000],
            "adverse_reactions": (r.get("adverse_reactions") or [""])[0][:1000],
        })
    tool_end("search_fda_drug_labels")
    return {"labels": labels}


@tool
def search_fda_drug_approvals(
    drug_name: str,
    limit: int = 3,
) -> dict:
    """Search FDA drug approval history (Drugs@FDA) for a given drug.

    Args:
        drug_name: Brand name of the drug.
        limit: Maximum number of results.

    Returns:
        Approval history including submissions, dates, and document links.
    """
    tool_start("search_fda_drug_approvals", {"drug_name": drug_name})
    url = f"{BASE}/drugsfda.json"
    params = _params(
        search=f'openfda.brand_name:"{drug_name}"',
        limit=min(limit, 10),
    )
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    results = data.get("results", [])
    drugs = []
    for r in results:
        openfda = r.get("openfda", {})
        submissions = []
        for s in r.get("submissions", [])[:10]:
            docs = [
                {"type": d.get("type"), "url": d.get("url"), "date": d.get("date")}
                for d in s.get("application_docs", [])[:5]
            ]
            submissions.append({
                "type": s.get("submission_type"),
                "number": s.get("submission_number"),
                "status": s.get("submission_status"),
                "status_date": s.get("submission_status_date"),
                "review_priority": s.get("review_priority"),
                "docs": docs,
            })
        drugs.append({
            "application_number": r.get("application_number"),
            "sponsor_name": r.get("sponsor_name"),
            "brand_name": openfda.get("brand_name", []),
            "substance_name": openfda.get("substance_name", []),
            "product_type": openfda.get("product_type", []),
            "submissions": submissions,
        })
    tool_end("search_fda_drug_approvals")
    return {"drugs": drugs}


@tool
def search_fda_recalls(
    query: str,
    limit: int = 10,
) -> dict:
    """Search FDA drug recall and enforcement actions.

    Args:
        query: Search query (drug name, firm name, or reason).
        limit: Maximum number of results.

    Returns:
        Recall/enforcement records with classification and reason.
    """
    tool_start("search_fda_recalls", {"query": query})
    url = f"{BASE}/enforcement.json"
    params = _params(search=query, limit=min(limit, 50))
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    results = data.get("results", [])
    recalls = []
    for r in results:
        recalls.append({
            "recall_number": r.get("recall_number"),
            "status": r.get("status"),
            "classification": r.get("classification"),
            "recalling_firm": r.get("recalling_firm"),
            "product_description": (r.get("product_description") or "")[:500],
            "reason_for_recall": r.get("reason_for_recall"),
            "initiation_date": r.get("recall_initiation_date"),
            "city": r.get("city"),
            "state": r.get("state"),
        })
    tool_end("search_fda_recalls")
    return {"total": data.get("meta", {}).get("results", {}).get("total", 0), "recalls": recalls}


@tool
def search_fda_shortages(
    limit: int = 20,
) -> dict:
    """Get current FDA drug shortage information.

    Args:
        limit: Maximum number of results.

    Returns:
        Drug shortage records with availability status and therapeutic category.
    """
    tool_start("search_fda_shortages")
    url = f"{BASE}/shortages.json"
    params: dict = {"limit": min(limit, 100)}
    if settings.openfda_api_key:
        params["api_key"] = settings.openfda_api_key
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    results = data.get("results", [])
    shortages = []
    for r in results:
        shortages.append({
            "generic_name": r.get("generic_name"),
            "availability": r.get("availability"),
            "update_type": r.get("update_type"),
            "update_date": r.get("update_date"),
            "therapeutic_category": r.get("therapeutic_category"),
            "brand_name": r.get("openfda", {}).get("brand_name", []),
            "manufacturer": r.get("openfda", {}).get("manufacturer_name", []),
        })
    tool_end("search_fda_shortages")
    return {"shortages": shortages}
