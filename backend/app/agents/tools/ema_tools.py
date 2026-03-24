"""EMA data tools for the Strands regulatory agent."""

import httpx
from strands import tool

from app.config import settings
from app.agents.event_stream import tool_start, tool_end

_TIMEOUT = 30.0

EMA_JSON_FILES = {
    "medicines": "medicines-output-medicines_json-report_en.json",
    "dhpc": "dhpc-output-json-report_en.json",
    "events": "events-json-report_en.json",
    "shortages": "shortages-output-json-report_en.json",
    "referrals": "referrals-output-json-report_en.json",
}


def _fetch_ema_json(dataset: str) -> list[dict]:
    filename = EMA_JSON_FILES.get(dataset)
    if not filename:
        raise ValueError(f"Unknown dataset: {dataset}")
    url = f"{settings.ema_base_url}/{filename}"
    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return resp.json()


@tool
def search_ema_medicines(
    query: str,
    limit: int = 10,
) -> dict:
    """Search EMA-authorised medicines by name, active substance, or therapeutic area.

    Args:
        query: Search term (medicine name, active substance, or therapeutic area).
        limit: Maximum number of results.

    Returns:
        Matching medicines with status, active substance, therapeutic area, and MAH.
    """
    tool_start("search_ema_medicines", {"query": query})
    data = _fetch_ema_json("medicines")
    query_lower = query.lower()
    matches = []
    for m in data:
        searchable = " ".join([
            m.get("name_of_medicine", ""),
            m.get("active_substance", ""),
            m.get("therapeutic_area_mesh", ""),
            m.get("therapeutic_indication", ""),
        ]).lower()
        if query_lower in searchable:
            matches.append({
                "name": m.get("name_of_medicine"),
                "active_substance": m.get("active_substance"),
                "status": m.get("medicine_status"),
                "therapeutic_area": m.get("therapeutic_area_mesh"),
                "indication": (m.get("therapeutic_indication") or "")[:500],
                "mah": m.get("marketing_authorisation_developer_applicant_holder"),
                "authorisation_date": m.get("marketing_authorisation_date"),
                "atc_code": m.get("atc_code_human"),
                "url": m.get("medicine_url"),
            })
            if len(matches) >= limit:
                break
    tool_end("search_ema_medicines")
    return {"total_found": len(matches), "medicines": matches}


@tool
def search_ema_safety_communications(
    query: str,
    limit: int = 10,
) -> dict:
    """Search EMA Direct Healthcare Professional Communications (DHPC) for safety alerts.

    Args:
        query: Search term (medicine name, active substance, or safety topic).
        limit: Maximum number of results.

    Returns:
        DHPC records with type, date, and related medicines.
    """
    tool_start("search_ema_safety_communications", {"query": query})
    data = _fetch_ema_json("dhpc")
    query_lower = query.lower()
    matches = []
    for d in data:
        searchable = " ".join([
            d.get("name_of_medicine", ""),
            d.get("active_substances", ""),
            d.get("dhpc_type", ""),
        ]).lower()
        if query_lower in searchable:
            matches.append({
                "medicine": d.get("name_of_medicine"),
                "active_substances": d.get("active_substances"),
                "dhpc_type": d.get("dhpc_type"),
                "dissemination_date": d.get("dissemination_date"),
                "atc_code": d.get("atc_code_human"),
                "url": d.get("dhpc_url"),
            })
            if len(matches) >= limit:
                break
    tool_end("search_ema_safety_communications")
    return {"total_found": len(matches), "dhpcs": matches}


@tool
def search_ema_events(
    query: str,
    limit: int = 10,
) -> dict:
    """Search upcoming EMA regulatory events, workshops, and meetings.

    Args:
        query: Search term (topic, event type).
        limit: Maximum number of results.

    Returns:
        Matching events with dates, location, and online availability.
    """
    tool_start("search_ema_events", {"query": query})
    data = _fetch_ema_json("events")
    query_lower = query.lower()
    matches = []
    for e in data:
        searchable = " ".join([
            e.get("title", ""),
            e.get("location", ""),
        ]).lower()
        if query_lower in searchable:
            matches.append({
                "title": e.get("title"),
                "dates": e.get("date_start_end_dates"),
                "online": e.get("online"),
                "location": e.get("location"),
                "url": e.get("event_url"),
            })
            if len(matches) >= limit:
                break
    tool_end("search_ema_events")
    return {"total_found": len(matches), "events": matches}


@tool
def search_ema_shortages(
    query: str,
    limit: int = 10,
) -> dict:
    """Search EMA drug shortage notifications.

    Args:
        query: Search term (medicine name or substance).
        limit: Maximum number of results.

    Returns:
        Drug shortage records from EMA.
    """
    tool_start("search_ema_shortages", {"query": query})
    data = _fetch_ema_json("shortages")
    query_lower = query.lower()
    matches = []
    for s in data:
        searchable = " ".join([
            str(s.get("name_of_medicine", "")),
            str(s.get("active_substance", "")),
        ]).lower()
        if query_lower in searchable:
            matches.append(s)
            if len(matches) >= limit:
                break
    tool_end("search_ema_shortages")
    return {"total_found": len(matches), "shortages": matches}


@tool
def search_ema_epi(
    medicine_name: str,
) -> dict:
    """Search EMA electronic Product Information (ePI) using the FHIR API.

    Args:
        medicine_name: Name of the medicine to search.

    Returns:
        ePI List resources with bundle references for the medicine.
    """
    tool_start("search_ema_epi", {"medicine_name": medicine_name})
    url = f"{settings.ema_epi_base_url}/List"
    params = {"title": medicine_name}
    with httpx.Client(timeout=_TIMEOUT) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    entries = data.get("entry", [])
    results = []
    for entry in entries[:10]:
        resource = entry.get("resource", {})
        subject = resource.get("subject", {})
        extensions = subject.get("extension", [])
        mah = ""
        procedure = ""
        for ext in extensions:
            ext_url = ext.get("url", "")
            if "marketingAuthorisationHolder" in ext_url:
                mah = ext.get("valueCoding", {}).get("display", "")
            elif "procedureNumber" in ext_url:
                procedure = ext.get("valueIdentifier", {}).get("value", "")
        bundles = [
            e.get("item", {}).get("reference", "")
            for e in resource.get("entry", [])
        ]
        results.append({
            "id": resource.get("id"),
            "title": resource.get("title"),
            "mah": mah,
            "procedure_number": procedure,
            "bundles": bundles,
        })
    tool_end("search_ema_epi")
    return {"total_found": len(results), "products": results}
