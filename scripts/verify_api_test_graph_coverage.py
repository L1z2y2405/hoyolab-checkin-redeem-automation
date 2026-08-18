#!/usr/bin/env python3
"""Verify [API-TEST] composite graph coverage from Datadog (live) or local cache.

Usage:
  cd critical-path-data-processing
  source venv/bin/activate
  python scripts/verify_api_test_graph_coverage.py
  python scripts/verify_api_test_graph_coverage.py --base-url http://127.0.0.1:8080
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

SOURCE_TAGS = [
    ("journey", "source:bcf-journey-composite-api-test"),
    ("business", "source:bcf-business-health-composite-api-test"),
    ("frontend", "source:bcf-frontend-health-composite-api-test"),
    ("payment", "source:bcf-payment-health-composite-api-test"),
    ("passwordless", "source:bcf-passwordless-auth-composite-api-test"),
    ("commerce", "source:bcf-commerce-health-composite-api-test"),
]

MARKETS = ("uk", "ca", "fr", "mx", "kw", "pr")


def fetch_groups(base_url: str, *, source_tag: str, live: bool) -> dict:
    params = urllib.parse.urlencode(
        {
            "stack": "dev",
            "name_prefix": "[API-TEST]",
            "source_tag": source_tag,
            "live": "true" if live else "false",
        }
    )
    url = f"{base_url.rstrip('/')}/api/datadog/monitors/composite-groups?{params}"
    with urllib.request.urlopen(url, timeout=120) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--live", action="store_true", help="Fetch monitors live from Datadog")
    args = parser.parse_args()

    print(f"Verifying graph coverage via {args.base_url} (live={args.live})")
    failures = 0

    for label, source_tag in SOURCE_TAGS:
        try:
            payload = fetch_groups(args.base_url, source_tag=source_tag, live=args.live)
        except urllib.error.HTTPError as exc:
            print(f"\n## {label}: HTTP {exc.code}")
            failures += 1
            continue
        except urllib.error.URLError as exc:
            print(f"\nBackend unavailable: {exc}")
            return 1

        groups = payload.get("groups") or []
        by_market: dict[str, list[dict]] = {market: [] for market in MARKETS}
        incomplete = 0

        for group in groups:
            market = str(group.get("market") or "").lower()
            if market in by_market:
                by_market[market].append(group)
            child_count = len(group.get("child_monitor_ids") or [])
            member_count = len(group.get("monitors") or [])
            expected_members = child_count + 1 + (1 if group.get("aggregate_monitor_id") else 0)
            if member_count < expected_members:
                incomplete += 1

        print(f"\n## {label} ({source_tag}) — {len(groups)} composites")
        for market in MARKETS:
            rows = by_market[market]
            names = [row.get("composite_name", "") for row in rows]
            print(f"  {market.upper():>2}: {len(rows):>2}  {', '.join(n[:40] for n in names[:2])}")
            if names and len(names) > 2:
                print(f"      … +{len(names) - 2} more")
        if incomplete:
            print(f"  WARNING: {incomplete} groups missing child nodes in cache")
            failures += 1

    print("\nDone.")
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
