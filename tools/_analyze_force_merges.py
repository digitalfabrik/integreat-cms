"""
Analyze force merges vs total merges for the integreat-cms repository.

A "force merge" is a PR that was merged while CI checks were failing.

Usage:
    export GITHUB_TOKEN="ghp_..."   # needs repo read access
    python3 tools/analyze_force_merges.py [--since 2025-10-01][--until 2026-01-13][--months 6] [--output csv]

Requires: requests (pip install requests)

Combination of time arguments: since | until | months
--since                         -> since = since; until = now
--since & --until               -> since = since; until = until
--since & --months              -> since = since; until = since + months
--since & --until (& --months)  -> since = since; until = until
--until                         -> invalid
--months                        -> since = now - months; until = now
--months & --until              -> since = until - months; until = until

"""

from __future__ import annotations

import argparse
import csv
import getpass
import io
import os
import sys
import time
from collections import defaultdict
from datetime import date, datetime, UTC

import requests

REPO = "digitalfabrik/integreat-cms"
API_BASE = "https://api.github.com"


def month_delta(date: date, months: int) -> date:
    return date.replace(
        month=((date.month + months - 1) % 12) + 1,
        year=date.year + ((date.month + months - 1) // 12),
    )


def construct_since_until(
    since_arg: date | None, until_arg: date | None, now: datetime, months: int
) -> tuple[date, date]:
    if since_arg:
        since = since_arg
        if until_arg:
            until = until_arg
            until = min(until, now.date())
        elif months:
            until = month_delta(now.date(), months)
            until = min(until, now.date())
        else:
            until = now.date()
    elif months:
        if until_arg:
            until = until_arg
            until = min(until, now.date())
            since = month_delta(until, -months)
        else:
            until = now.date()
            since = month_delta(now.date(), -months)
    return (since, until)


def get_session(token: str) -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )
    return session


def validate_token(session: requests.Session) -> None:
    response = session.get("https://api.github.com/user")

    if response.status_code == 401:
        raise ValueError("Invalid GitHub token (401 Unauthorized).")

    if response.status_code == 403:
        raise ValueError("Token does not have required permissions.")

    response.raise_for_status()


def handle_rate_limit(response: requests.Response) -> None:
    remaining = int(response.headers.get("X-RateLimit-Remaining", 1))
    if remaining < 5:
        reset_ts = int(response.headers.get("X-RateLimit-Reset", 0))
        wait = max(reset_ts - int(time.time()), 1) + 1
        print(f"  Rate limit nearly exhausted, waiting {wait}s...", file=sys.stderr)
        time.sleep(wait)


def get_merged_prs(session: requests.Session, since: date, until: date) -> list[dict]:
    """Fetch all merged PRs since the given date."""
    prs = []
    page = 1
    per_page = 100

    while True:
        print(f"  Fetching merged PRs page {page}...", file=sys.stderr)
        resp = session.get(
            f"{API_BASE}/repos/{REPO}/pulls",
            params={
                "state": "closed",
                "base": "develop",
                "sort": "updated",
                "direction": "desc",
                "per_page": str(per_page),
                "page": str(page),
            },
        )
        resp.raise_for_status()
        handle_rate_limit(resp)

        batch = resp.json()
        if not batch:
            break

        found_old = False
        for pr in batch:
            if not pr.get("merged_at"):
                continue
            merged_at = datetime.fromisoformat(
                pr["merged_at"].replace("Z", "+00:00")
            ).date()
            if merged_at > until:
                continue
            if merged_at < since:
                found_old = True
                break
            prs.append(pr)

        if found_old or len(batch) < per_page:
            break
        page += 1

    return prs


def get_commit_status(session: requests.Session, sha: str) -> dict:
    """Get combined status and check runs for a commit."""
    # Combined status (legacy status API)
    status_resp = session.get(f"{API_BASE}/repos/{REPO}/commits/{sha}/status")
    status_resp.raise_for_status()
    handle_rate_limit(status_resp)
    combined_status = status_resp.json()

    # Check runs (GitHub Actions / CircleCI checks API)
    checks_resp = session.get(
        f"{API_BASE}/repos/{REPO}/commits/{sha}/check-runs",
        params={"per_page": 100},
    )
    checks_resp.raise_for_status()
    handle_rate_limit(checks_resp)
    check_runs = checks_resp.json()

    return {
        "combined_state": combined_status.get("state", "unknown"),
        "statuses": combined_status.get("statuses", []),
        "check_runs": check_runs.get("check_runs", []),
    }


def classify_pr(status_info: dict) -> str:
    """
    Classify a PR's CI status at merge time.

    Returns one of: "passing", "failing", "pending", "no_checks"
    """
    statuses = status_info["statuses"]
    check_runs = status_info["check_runs"]

    if not statuses and not check_runs:
        return "no_checks"

    has_failure = False
    has_pending = False

    # Check legacy statuses (CircleCI often reports here)
    for status in statuses:
        state = status.get("state", "")
        if state in ("failure", "error"):
            has_failure = True
        elif state == "pending":
            has_pending = True

    # Check runs (GitHub Checks API)
    for check_run in check_runs:
        conclusion = check_run.get("conclusion")
        status = check_run.get("status")
        if conclusion in ("failure", "timed_out", "action_required"):
            has_failure = True
        elif status != "completed":
            has_pending = True

    if has_failure:
        return "failing"
    if has_pending:
        return "pending"
    return "passing"


def classify_each_pr(prs: list[dict], session: requests.Session) -> list[dict]:
    results = []
    for i, pr in enumerate(prs):
        sha = pr["head"]["sha"]
        merged_by = pr.get("merged_by", {}).get("login", "unknown")

        print(
            f"  Checking PR #{pr['number']} ({i + 1}/{len(prs)})...",
            file=sys.stderr,
        )

        status_info = get_commit_status(session, sha)
        classification = classify_pr(status_info)
        results.append(
            {
                "number": pr["number"],
                "title": pr["title"],
                "merged_at": pr["merged_at"],
                "merged_by": merged_by,
                "sha": sha[:8],
                "status": classification,
                "failing_checks": (
                    get_failing_check_names(status_info)
                    if classification == "failing"
                    else []
                ),
            }
        )
    return results


def get_failing_check_names(status_info: dict) -> list[str]:
    """Get names of failing checks."""
    names = [
        status.get("context", "unknown")
        for status in status_info["statuses"]
        if status.get("state") in ("failure", "error")
    ]
    names.extend(
        check_run.get("name", "unknown")
        for check_run in status_info["check_runs"]
        if check_run.get("conclusion") in ("failure", "timed_out", "action_required")
    )
    return names


def print_csv(sorted_months: list[str], monthly: dict[str, dict[str, int]]) -> None:
    """Print results in CSV format."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "month",
            "total_merges",
            "passing",
            "failing",
            "pending",
            "no_checks",
            "force_merge_rate",
        ]
    )
    for month in sorted_months:
        d = monthly[month]
        rate = f"{d['failing'] / d['total'] * 100:.1f}%" if d["total"] else "0.0%"
        writer.writerow(
            [
                month,
                d["total"],
                d["passing"],
                d["failing"],
                d["pending"],
                d["no_checks"],
                rate,
            ]
        )
    print(buf.getvalue())


def print_table(sorted_months: list[str], monthly: dict[str, dict[str, int]]) -> None:
    """Print results as a formatted ASCII table."""
    print()
    print(
        f"{'Month':<10} {'Total':>6} {'Pass':>6} {'Fail':>6} {'Pending':>8} {'No CI':>6} {'Force Merge %':>14}"
    )
    print("-" * 62)

    total_all = 0
    total_failing = 0
    for month in sorted_months:
        d = monthly[month]
        rate = d["failing"] / d["total"] * 100 if d["total"] else 0.0
        total_all += d["total"]
        total_failing += d["failing"]
        print(
            f"{month:<10} {d['total']:>6} {d['passing']:>6} {d['failing']:>6} "
            f"{d['pending']:>8} {d['no_checks']:>6} {rate:>13.1f}%"
        )

    print("-" * 62)
    overall_rate = total_failing / total_all * 100 if total_all else 0.0
    print(
        f"{'TOTAL':<10} {total_all:>6} {'':>6} {total_failing:>6} "
        f"{'':>8} {'':>6} {overall_rate:>13.1f}%"
    )
    print()


def print_detail(results: list[dict]) -> None:
    """Print details for each force-merged PR."""
    force_merged = [result for result in results if result["status"] == "failing"]
    if force_merged:
        print("Force-merged PRs (merged with failing CI):")
        print("-" * 80)
        for pr in sorted(force_merged, key=lambda x: x["merged_at"]):
            print(
                f"  #{pr['number']:<6} {pr['merged_at'][:10]}  "
                f"by {pr['merged_by']:<16} {pr['title'][:50]}"
            )
            if pr["failing_checks"]:
                print(f"           Failing: {', '.join(pr['failing_checks'][:5])}")
        print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze force merges (merges with failing CI)"
    )
    parser.add_argument(
        "--since",
        help="Start Date of calculation - follow format: YYYY-mm-dd",
    )
    parser.add_argument(
        "--until",
        help="End Date of calculation - follow format: YYYY-mm-dd",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=6,
        help="How many months back to analyze (default 6)",
    )
    parser.add_argument(
        "--output",
        choices=["table", "csv"],
        default="table",
        help="Output format (default: table)",
    )
    parser.add_argument(
        "--detail",
        action="store_true",
        help="Show details for each force-merged PR",
    )
    args = parser.parse_args()

    now = datetime.now(UTC)

    # validate arguments
    since_arg = None
    until_arg = None
    if args.since:
        try:
            since_arg = datetime.strptime(args.since, "%Y-%m-%d").date()
            if since_arg >= now.date():
                print("Since needs to be before Today")
                return 2
        except ValueError:
            print("Wrong date format for 'since' date, please use YYYY-MM-DD")
            return 2
    if args.until:
        try:
            until_arg = datetime.strptime(args.until, "%Y-%m-%d").date()
        except ValueError:
            print("Wrong date format for 'until' date, please use YYYY-MM-DD")
            return 2
    if since_arg and until_arg and until_arg < since_arg:
        print("The '--until' date cannot be before the 'since' date")
        return 2
    if until_arg and not since_arg and not args.months:
        print(
            "Either a '--months' duration or a '--since' date needs to be provided alongside the '--until' date"
        )
        return 2

    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        print("GITHUB_TOKEN environment variable not found.")
        try:
            token = getpass.getpass(
                "Please enter your GitHub token (input hidden): "
            ).strip()
        except KeyboardInterrupt:
            print("\nAborted.")
            return 1

        if not token:
            print("Error: No token provided.", file=sys.stderr)
            return 1

        # Set it for this process (and child processes)
        os.environ["GITHUB_TOKEN"] = token

    session = get_session(token)
    try:
        validate_token(session)
    except ValueError as e:
        print(f"Authentication error: {e}", file=sys.stderr)
        return 1

    # construct correct 'since' and 'until' vars
    since, until = construct_since_until(since_arg, until_arg, now, args.months)

    print(f"Analyzing PRs merged between {since} and {until}", file=sys.stderr)

    # Fetch merged PRs
    prs = get_merged_prs(session, since, until)
    print(f"Found {len(prs)} merged PRs.", file=sys.stderr)

    if not prs:
        print("No merged PRs found in the given time range.")
        return 0

    # Classify each PR
    results = classify_each_pr(prs, session)

    # Aggregate by month
    monthly: dict[str, dict[str, int]] = defaultdict(
        lambda: {"total": 0, "passing": 0, "failing": 0, "pending": 0, "no_checks": 0}
    )
    for result in results:
        month_key = result["merged_at"][:7]  # YYYY-MM
        monthly[month_key]["total"] += 1
        monthly[month_key][result["status"]] += 1

    sorted_months = sorted(monthly.keys())

    if args.output == "csv":
        print_csv(sorted_months, monthly)
    else:
        print_table(sorted_months, monthly)

    if args.detail:
        print_detail(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
