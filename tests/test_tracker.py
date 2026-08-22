"""
Tests for src/tracker.py — the application tracker module.

Each test points APPLICATIONS_FILE at a temp file so we never touch the
user's real data/applications.json.
"""

import importlib

import pytest

import src.config as config
import src.tracker as tracker


@pytest.fixture(autouse=True)
def isolated_applications_file(tmp_path, monkeypatch):
    """Redirect the tracker's storage to a throwaway file for every test."""
    temp_file = tmp_path / "applications.json"
    monkeypatch.setattr(config, "APPLICATIONS_FILE", temp_file)
    monkeypatch.setattr(tracker, "APPLICATIONS_FILE", temp_file)
    yield temp_file


def test_load_applications_empty_when_no_file():
    assert tracker.load_applications() == []


def test_add_application_persists_and_returns_record():
    record = tracker.add_application(
        title="Embedded Software Engineer",
        company="Acme Robotics",
        location="Los Angeles, CA",
        status="applied",
        date_applied="2026-08-01",
    )

    assert record["title"] == "Embedded Software Engineer"
    assert record["company"] == "Acme Robotics"
    assert record["status"] == "applied"
    assert record["id"]
    assert record["status_history"] == [{"status": "applied", "date": "2026-08-01"}]

    stored = tracker.load_applications()
    assert len(stored) == 1
    assert stored[0]["id"] == record["id"]


def test_add_application_rejects_invalid_status():
    with pytest.raises(ValueError):
        tracker.add_application(title="X", company="Y", status="not-a-real-status")


def test_update_status_changes_status_and_appends_history():
    record = tracker.add_application(
        title="Firmware Engineer", company="Orbital Co", date_applied="2026-07-01"
    )

    updated = tracker.update_status(record["id"], "interviewing")

    assert updated["status"] == "interviewing"
    assert len(updated["status_history"]) == 2
    assert updated["status_history"][-1]["status"] == "interviewing"


def test_update_status_unknown_id_raises():
    with pytest.raises(ValueError):
        tracker.update_status("nonexistent", "offer")


def test_update_status_invalid_status_raises():
    record = tracker.add_application(title="X", company="Y")
    with pytest.raises(ValueError):
        tracker.update_status(record["id"], "not-a-real-status")


def test_list_applications_filters_by_status():
    tracker.add_application(title="A", company="C1", status="applied")
    tracker.add_application(title="B", company="C2", status="interviewing")

    applied_only = tracker.list_applications(status_filter="applied")
    assert len(applied_only) == 1
    assert applied_only[0]["company"] == "C1"


def test_list_applications_sorted_most_recent_first():
    tracker.add_application(title="Old", company="C1", date_applied="2026-01-01")
    tracker.add_application(title="New", company="C2", date_applied="2026-06-01")

    results = tracker.list_applications()
    assert results[0]["title"] == "New"
    assert results[1]["title"] == "Old"


def test_compute_stats_on_empty_data():
    stats = tracker.compute_stats([])
    assert stats["total"] == 0
    assert stats["response_rate"] == 0.0
    assert stats["offer_rate"] == 0.0
    assert all(count == 0 for count in stats["by_status"].values())


def test_compute_stats_response_and_offer_rate():
    tracker.add_application(title="A", company="C1", status="applied")
    tracker.add_application(title="B", company="C2", status="interviewing")
    tracker.add_application(title="C", company="C3", status="offer")
    tracker.add_application(title="D", company="C4", status="rejected")

    stats = tracker.compute_stats()

    assert stats["total"] == 4
    # 3 of 4 applications got SOME response (interviewing/offer/rejected)
    assert stats["response_rate"] == 75.0
    assert stats["offer_rate"] == 25.0
    assert stats["by_status"]["applied"] == 1
    assert stats["by_status"]["offer"] == 1


def test_compute_stats_top_companies():
    tracker.add_application(title="A", company="Acme", status="applied")
    tracker.add_application(title="B", company="Acme", status="applied")
    tracker.add_application(title="C", company="Beta Corp", status="applied")

    stats = tracker.compute_stats()
    top = dict(stats["top_companies"])
    assert top["Acme"] == 2
    assert top["Beta Corp"] == 1


def test_format_stats_report_handles_zero_applications():
    report = tracker.format_stats_report(tracker.compute_stats([]))
    assert "No applications tracked yet" in report


def test_format_stats_report_includes_key_numbers():
    tracker.add_application(title="A", company="Acme", status="offer")
    report = tracker.format_stats_report(tracker.compute_stats())
    assert "Total applications: 1" in report
    assert "Offer rate: 100.0%" in report
