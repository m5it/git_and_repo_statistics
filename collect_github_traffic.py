#!/usr/bin/env python3
"""
Collect GitHub traffic insights for all repos of a user.
Saves clones and views per repo to traffic_YYYY-MM-DD.txt
Usage: GITHUB_TOKEN=your_token python collect_github_traffic.py [username]
"""
import os
import sys
import json
import requests
from datetime import datetime, timezone
from pathlib import Path

TOKEN = os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    print("Error: set GITHUB_TOKEN environment variable", file=sys.stderr)
    sys.exit(1)

USER = sys.argv[1] if len(sys.argv) > 1 else "m5it"
BASE = "https://api.github.com"
HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}

OUT_DIR = Path("traffic_reports")
OUT_DIR.mkdir(exist_ok=True)
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
OUT_FILE = OUT_DIR / f"traffic_{TODAY}.txt"


def get_all_repos(user):
    repos = []
    page = 1
    while True:
        url = f"{BASE}/users/{user}/repos?per_page=100&page={page}"
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos


def get_traffic(owner, repo, kind):
    url = f"{BASE}/repos/{owner}/{repo}/traffic/{kind}"
    r = requests.get(url, headers=HEADERS, timeout=30)
    if r.status_code == 404:
        return None  # traffic not available (e.g. private/no access)
    r.raise_for_status()
    return r.json()


def main():
    print(f"Fetching repos for {USER}...")
    repos = get_all_repos(USER)
    print(f"Found {len(repos)} repos")

    lines = [f"# GitHub Traffic Report for {USER}", f"# Date: {TODAY}", f"# Repos: {len(repos)}", ""]
    total_clones = 0
    total_unique_cloners = 0
    total_views = 0
    total_unique_visitors = 0

    for repo in sorted(repos, key=lambda x: x["name"]):
        name = repo["name"]
        print(f"  -> {name}")
        clones = get_traffic(USER, name, "clones")
        views = get_traffic(USER, name, "views")

        lines.append(f"## {name}")
        lines.append(f"URL: {repo['html_url']}")
        lines.append(f"Private: {repo['private']}")
        lines.append(f"Created: {repo['created_at']}")
        lines.append(f"Updated: {repo['updated_at']}")

        if clones:
            c_total = clones.get("count", 0)
            c_unique = clones.get("uniques", 0)
            total_clones += c_total
            total_unique_cloners += c_unique
            lines.append(f"Clones (14d): {c_total} total, {c_unique} unique")
            for day in clones.get("clones", []):
                ts = day["timestamp"][:10]
                lines.append(f"  {ts}: {day['count']} clones, {day['uniques']} unique")
        else:
            lines.append("Clones (14d): N/A")

        if views:
            v_total = views.get("count", 0)
            v_unique = views.get("uniques", 0)
            total_views += v_total
            total_unique_visitors += v_unique
            lines.append(f"Views (14d): {v_total} total, {v_unique} unique")
            for day in views.get("views", []):
                ts = day["timestamp"][:10]
                lines.append(f"  {ts}: {day['count']} views, {day['uniques']} unique")
        else:
            lines.append("Views (14d): N/A")

        lines.append("")

    lines.append("## Summary")
    lines.append(f"Total clones: {total_clones}")
    lines.append(f"Total unique cloners: {total_unique_cloners}")
    lines.append(f"Total views: {total_views}")
    lines.append(f"Total unique visitors: {total_unique_visitors}")

    OUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nSaved report to: {OUT_FILE}")


if __name__ == "__main__":
    main()
