"""EMA data tools for the Strands regulatory agent."""

import logging
import threading
import time

import httpx
from strands import tool

from app.config import settings
from app.agents.event_stream import tool_start, tool_end

logger = logging.getLogger(__name__)

_TIMEOUT = 60.0
_MAX_RETRIES = 3
_INITIAL_BACKOFF = 2.0  # seconds
_REQUEST_INTERVAL = 1.5  # seconds between requests to avoid 429

EMA_JSON_FILES = {
    "medicines": "medicines-output-medicines_json-report_en.json",
    "dhpc": "dhpc-output-json-report_en.json",
    "events": "events-json-report_en.json",
    "shortages": "shortages-output-json-report_en.json",
    "referrals": "referrals-output-json-report_en.json",
}

_rate_lock = threading.Lock()
_last_request_time: float = 0.0


def _wait_for_rate_limit():
    """Wait if needed to respect the minimum interval between EMA requests."""
    global _last_request_time
    with _rate_lock:
        now = time.monotonic()
        elapsed = now - _last_request_time
        if _last_request_time > 0 and elapsed < _REQUEST_INTERVAL:
            time.sleep(_REQUEST_INTERVAL - elapsed)
        _last_request_time = time.monotonic()


def _fetch_ema_json(dataset: str) -> list[dict]:
    filename = EMA_JSON_FILES.get(dataset)
    if not filename:
        raise ValueError(f"Unknown dataset: {dataset}")
    url = f"{settings.ema_base_url}/{filename}"

    for attempt in range(_MAX_RETRIES):
        _wait_for_rate_limit()
        try:
            with httpx.Client(timeout=_TIMEOUT, follow_redirects=True) as client:
                resp = client.get(url)
                if resp.status_code == 429:
                    backoff = _INITIAL_BACKOFF * (2 ** attempt)
                    logger.warning(
                        "EMA 429 rate-limited for %s, retrying in %.1fs (attempt %d/%d)",
                        dataset, backoff, attempt + 1, _MAX_RETRIES,
                    )
                    time.sleep(backoff)
                    continue
                resp.raise_for_status()
                payload = resp.json()
                if isinstance(payload, dict) and "data" in payload:
                    return payload["data"]
                return payload
        except httpx.TimeoutException:
            if attempt < _MAX_RETRIES - 1:
                backoff = _INITIAL_BACKOFF * (2 ** attempt)
                logger.warning(
                    "EMA timeout for %s, retrying in %.1fs (attempt %d/%d)",
                    dataset, backoff, attempt + 1, _MAX_RETRIES,
                )
                time.sleep(backoff)
            else:
                raise

    raise httpx.HTTPStatusError(
        f"EMA API rate-limited after {_MAX_RETRIES} retries",
        request=httpx.Request("GET", url),
        response=resp,
    )


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
            str(s.get("medicine_affected", "")),
            str(s.get("international_non_proprietary_name_inn_or_common_name", "")),
        ]).lower()
        if query_lower in searchable:
            matches.append(s)
            if len(matches) >= limit:
                break
    tool_end("search_ema_shortages")
    return {"total_found": len(matches), "shortages": matches}
