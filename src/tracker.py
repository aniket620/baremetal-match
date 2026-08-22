"""
Application tracker for BareMetal Match.

This module is independent of the CrewAI pipeline in main.py — it's a
lightweight personal log of the jobs you've actually applied to, with status
tracking (applied / interviewing / offer / rejected / ghosted / withdrawn)
and summary stats (response rate, offer rate, pipeline breakdown, recent
activity, top companies).

Data is stored as JSON in DATA_DIR (see src/config.py), which is gitignored
by default since it's personal application history, not project code.

Use track.py at the repo root as the command-line interface to this module.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, date
from pathlib import Path

from src.config import APPLICATIONS_FILE


# =============================================================================
# STATUS DEFINITIONS
# =============================================================================

# Ordered roughly by how far along the pipeline an application has gotten.
STATUSES = ["applied", "interviewing", "offer", "rejected", "ghosted", "withdrawn"]

# Statuses that count as "the company responded" for response-rate purposes.
RESPONDED_STATUSES = {"interviewing", "offer", "rejected"}

DATE_FORMAT = "%Y-%m-%d"


# =============================================================================
# STORAGE
# =============================================================================

def _today_str() -> str:
    return date.today().strftime(DATE_FORMAT)


def load_applications() -> list[dict]:
    """Load all tracked applications from disk. Returns [] if none yet."""
    if not APPLICATIONS_FILE.exists():
        return []
    with open(APPLICATIONS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_applications(applications: list[dict]) -> None:
    """Persist all tracked applications to disk."""
    APPLICATIONS_FILE.parent.mkdir(exist_ok=True)
    with open(APPLICATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(applications, f, indent=2)


# =============================================================================
# CRUD OPERATIONS
# =============================================================================

def add_application(
    title: str,
    company: str,
    location: str = "",
    url: str = "",
    status: str = "applied",
    notes: str = "",
    date_applied: str | None = None,
) -> dict:
    """
    Add a new application to the tracker.

    Args:
        title: Job title (e.g. "Embedded Software Engineer")
        company: Company name
        location: Job location (optional)
        url: Application/listing URL (optional)
        status: Initial status, defaults to "applied"
        notes: Freeform notes (optional)
        date_applied: Date in YYYY-MM-DD format, defaults to today

    Returns:
        The newly created application record (also persisted to disk)
    """
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}, got {status!r}")

    applications = load_applications()

    record = {
        "id": uuid.uuid4().hex[:8],
        "title": title,
        "company": company,
        "location": location,
        "url": url,
        "status": status,
        "notes": notes,
        "date_applied": date_applied or _today_str(),
        "last_updated": _today_str(),
        "status_history": [{"status": status, "date": date_applied or _today_str()}],
    }

    applications.append(record)
    save_applications(applications)
    return record


def update_status(application_id: str, new_status: str) -> dict:
    """
    Update the status of an existing application.

    Args:
        application_id: The short id (see list_applications output)
        new_status: One of STATUSES

    Returns:
        The updated application record

    Raises:
        ValueError: If the id doesn't exist or the status is invalid
    """
    if new_status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}, got {new_status!r}")

    applications = load_applications()
    for app in applications:
        if app["id"] == application_id:
            app["status"] = new_status
            app["last_updated"] = _today_str()
            app.setdefault("status_history", []).append(
                {"status": new_status, "date": _today_str()}
            )
            save_applications(applications)
            return app

    raise ValueError(f"No application found with id {application_id!r}")


def list_applications(status_filter: str | None = None) -> list[dict]:
    """
    List tracked applications, optionally filtered by status.

    Args:
        status_filter: If set, only return applications with this status

    Returns:
        List of application records, most recently applied first
    """
    applications = load_applications()
    if status_filter:
        applications = [a for a in applications if a["status"] == status_filter]
    return sorted(applications, key=lambda a: a["date_applied"], reverse=True)


# =============================================================================
# STATS
# =============================================================================

def compute_stats(applications: list[dict] | None = None) -> dict:
    """
    Compute summary statistics across all tracked applications.

    Returns a dict with:
        total: total number of applications
        by_status: {status: count} for every status, including zero-count ones
        response_rate: % of applications that got ANY response (interviewing/
            offer/rejected) out of total applied
        offer_rate: % of applications that resulted in an offer
        last_7_days / last_30_days: applications submitted in that window
        top_companies: [(company, count), ...] sorted descending, top 5
        avg_days_to_first_response: average days between date_applied and the
            first status change away from "applied" (None if no data)
    """
    if applications is None:
        applications = load_applications()

    total = len(applications)
    by_status = {s: 0 for s in STATUSES}
    for app in applications:
        by_status[app["status"]] = by_status.get(app["status"], 0) + 1

    responded = sum(
        1 for a in applications if a["status"] in RESPONDED_STATUSES
    )
    offers = by_status.get("offer", 0)

    response_rate = round(100 * responded / total, 1) if total else 0.0
    offer_rate = round(100 * offers / total, 1) if total else 0.0

    today = date.today()
    last_7_days = 0
    last_30_days = 0
    for a in applications:
        try:
            applied_date = datetime.strptime(a["date_applied"], DATE_FORMAT).date()
        except (ValueError, KeyError):
            continue
        days_ago = (today - applied_date).days
        if days_ago <= 7:
            last_7_days += 1
        if days_ago <= 30:
            last_30_days += 1

    company_counts: dict[str, int] = {}
    for a in applications:
        company_counts[a["company"]] = company_counts.get(a["company"], 0) + 1
    top_companies = sorted(company_counts.items(), key=lambda kv: kv[1], reverse=True)[:5]

    response_days = []
    for a in applications:
        history = a.get("status_history", [])
        if len(history) < 2:
            continue
        try:
            applied_date = datetime.strptime(history[0]["date"], DATE_FORMAT).date()
            response_date = datetime.strptime(history[1]["date"], DATE_FORMAT).date()
        except (ValueError, KeyError, IndexError):
            continue
        response_days.append((response_date - applied_date).days)

    avg_days_to_first_response = (
        round(sum(response_days) / len(response_days), 1) if response_days else None
    )

    return {
        "total": total,
        "by_status": by_status,
        "response_rate": response_rate,
        "offer_rate": offer_rate,
        "last_7_days": last_7_days,
        "last_30_days": last_30_days,
        "top_companies": top_companies,
        "avg_days_to_first_response": avg_days_to_first_response,
    }


# =============================================================================
# FORMATTING
# =============================================================================

_STATUS_EMOJI = {
    "applied": "📨",
    "interviewing": "🎤",
    "offer": "🎉",
    "rejected": "❌",
    "ghosted": "👻",
    "withdrawn": "🚫",
}


def _bar(count: int, max_count: int, width: int = 30) -> str:
    if max_count == 0:
        return ""
    filled = round(width * count / max_count)
    return "█" * filled + "░" * (width - filled)


def format_stats_report(stats: dict) -> str:
    """Render the stats dict as a human-readable text report."""
    lines = []
    lines.append("=" * 60)
    lines.append("📊 BAREMETAL MATCH — APPLICATION STATS")
    lines.append("=" * 60)
    lines.append(f"\nTotal applications: {stats['total']}")

    if stats["total"] == 0:
        lines.append("\nNo applications tracked yet. Add one with:")
        lines.append('  uv run track.py add --title "..." --company "..."')
        lines.append("=" * 60)
        return "\n".join(lines)

    lines.append(f"Response rate: {stats['response_rate']}% (interview, offer, or rejection)")
    lines.append(f"Offer rate: {stats['offer_rate']}%")
    if stats["avg_days_to_first_response"] is not None:
        lines.append(f"Avg. days to first response: {stats['avg_days_to_first_response']}")
    lines.append(f"\nApplications in last 7 days: {stats['last_7_days']}")
    lines.append(f"Applications in last 30 days: {stats['last_30_days']}")

    lines.append("\nPipeline breakdown:")
    max_count = max(stats["by_status"].values()) if stats["by_status"] else 0
    for status in STATUSES:
        count = stats["by_status"].get(status, 0)
        emoji = _STATUS_EMOJI.get(status, "")
        bar = _bar(count, max_count)
        lines.append(f"  {emoji} {status:<14} {bar} {count}")

    if stats["top_companies"]:
        lines.append("\nTop companies applied to:")
        for company, count in stats["top_companies"]:
            lines.append(f"  - {company}: {count}")

    lines.append("=" * 60)
    return "\n".join(lines)


__all__ = [
    "STATUSES",
    "load_applications",
    "save_applications",
    "add_application",
    "update_status",
    "list_applications",
    "compute_stats",
    "format_stats_report",
]
