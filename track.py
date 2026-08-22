#!/usr/bin/env python3
"""
BareMetal Match — Application Tracker CLI

A lightweight, separate command-line tool for logging the embedded
engineering jobs you've actually applied to and seeing stats about your
pipeline. This is independent of main.py's AI job search — main.py finds and
prepares you for jobs; track.py records what you actually did about them.

Usage:
    # Log a new application
    uv run track.py add --title "Embedded Software Engineer" --company "Anduril" \\
        --location "Costa Mesa, CA" --url "https://..." --notes "Referred by Jane"

    # Update an application's status (use the id shown by `list`/`add`)
    uv run track.py update a1b2c3d4 --status interviewing

    # List tracked applications (optionally filtered)
    uv run track.py list
    uv run track.py list --status interviewing

    # Show pipeline stats
    uv run track.py stats
"""

import argparse
import sys

from src.tracker import (
    STATUSES,
    add_application,
    update_status,
    list_applications,
    compute_stats,
    format_stats_report,
)


def cmd_add(args: argparse.Namespace) -> None:
    record = add_application(
        title=args.title,
        company=args.company,
        location=args.location or "",
        url=args.url or "",
        status=args.status,
        notes=args.notes or "",
        date_applied=args.date,
    )
    print(f"✅ Logged application [{record['id']}]: {record['title']} @ {record['company']}")
    print(f"   Status: {record['status']} | Applied: {record['date_applied']}")


def cmd_update(args: argparse.Namespace) -> None:
    try:
        record = update_status(args.id, args.status)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    print(f"✅ Updated [{record['id']}]: {record['title']} @ {record['company']} -> {record['status']}")


def cmd_list(args: argparse.Namespace) -> None:
    applications = list_applications(status_filter=args.status)

    if not applications:
        if args.status:
            print(f"No applications with status '{args.status}'.")
        else:
            print("No applications tracked yet. Add one with `uv run track.py add ...`")
        return

    print(f"\n{'ID':<10}{'Status':<14}{'Applied':<12}{'Title':<35}{'Company':<20}")
    print("-" * 91)
    for app in applications:
        print(
            f"{app['id']:<10}{app['status']:<14}{app['date_applied']:<12}"
            f"{app['title'][:33]:<35}{app['company'][:18]:<20}"
        )
    print()


def cmd_stats(args: argparse.Namespace) -> None:
    stats = compute_stats()
    print(format_stats_report(stats))


def main():
    parser = argparse.ArgumentParser(
        description="BareMetal Match — track your job applications and see your stats."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_add = subparsers.add_parser("add", help="Log a new application")
    p_add.add_argument("--title", required=True, help="Job title")
    p_add.add_argument("--company", required=True, help="Company name")
    p_add.add_argument("--location", help="Job location")
    p_add.add_argument("--url", help="Listing/application URL")
    p_add.add_argument("--notes", help="Freeform notes")
    p_add.add_argument("--date", help="Date applied (YYYY-MM-DD), defaults to today")
    p_add.add_argument(
        "--status", choices=STATUSES, default="applied",
        help="Initial status (default: applied)"
    )
    p_add.set_defaults(func=cmd_add)

    p_update = subparsers.add_parser("update", help="Update an application's status")
    p_update.add_argument("id", help="Application id (shown by `list`/`add`)")
    p_update.add_argument("--status", required=True, choices=STATUSES)
    p_update.set_defaults(func=cmd_update)

    p_list = subparsers.add_parser("list", help="List tracked applications")
    p_list.add_argument("--status", choices=STATUSES, help="Filter by status")
    p_list.set_defaults(func=cmd_list)

    p_stats = subparsers.add_parser("stats", help="Show pipeline stats")
    p_stats.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
