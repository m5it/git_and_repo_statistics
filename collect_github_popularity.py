#!/usr/bin/env python3
"""
Collect public popularity stats for any GitHub user(s).
Usage:
  GITHUB_TOKEN=your_token python collect_github_popularity.py <username>
  GITHUB_TOKEN=your_token python collect_github_popularity.py --list users.txt
  GITHUB_TOKEN=your_token python collect_github_popularity.py -l competitors.txt
Outputs:
  - popularity_reports/popularity_USERNAME_YYYY-MM-DD.txt
  - popularity_reports/history_USERNAME.csv  (appended daily, great for graphs)
"""
import os
import sys
import json
import csv
import requests
import argparse
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github.v3+json",
}

OUT_DIR = Path("popularity_reports")
OUT_DIR.mkdir(exist_ok=True)
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")


def load_token():
    # 1. Environment variable
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    # 2. File ~/.github_token
    token_file = Path.home() / ".github_token"
    if token_file.exists():
        return token_file.read_text().strip()
    # 3. File .env in current directory
    env_file = Path(".env")
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.startswith("GITHUB_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"\'')
    return None


def api_get(url, token):
    r = requests.get(url, headers={**HEADERS, "Authorization": f"token {token}"}, timeout=30)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def get_all_repos(user, token):
    repos = []
    page = 1
    while True:
        url = f"{BASE}/users/{user}/repos?per_page=100&page={page}&sort=updated"
        data = api_get(url, token)
        if data is None:
            return None
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos


def append_history_csv(user, repo_stats):
    HISTORY_CSV = OUT_DIR / f"history_{user}.csv"
    fieldnames = ["date", "repo", "url", "stars", "forks", "watchers", "issues", "language", "updated"]
    file_exists = HISTORY_CSV.exists()

    with HISTORY_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        for r in repo_stats:
            writer.writerow({
                "date": TODAY,
                "repo": r["name"],
                "url": r["url"],
                "stars": r["stars"],
                "forks": r["forks"],
                "watchers": r["watchers"],
                "issues": r["issues"],
                "language": r["language"],
                "updated": r["updated"],
            })


def process_user(user, token):
    print(f"\n{'='*50}")
    print(f"Fetching public repos for {user}...")
    repos = get_all_repos(user, token)
    if repos is None:
        print(f"  User '{user}' not found or no public repos.")
        return False

    print(f"Found {len(repos)} public repos")

    OUT_FILE = OUT_DIR / f"popularity_{user}_{TODAY}.txt"
    lines = [f"# GitHub Popularity Report for {user}", f"# Date: {TODAY}", f"# Public repos: {len(repos)}", ""]

    total_stars = 0
    total_forks = 0
    total_open_issues = 0

    repo_stats = []
    for repo in sorted(repos, key=lambda x: x["stargazers_count"], reverse=True):
        name = repo["name"]
        stars = repo.get("stargazers_count", 0)
        forks = repo.get("forks_count", 0)
        watchers = repo.get("watchers_count", 0)
        issues = repo.get("open_issues_count", 0)
        created = repo.get("created_at", "")[:10]
        updated = repo.get("updated_at", "")[:10]
        size = repo.get("size", 0)
        language = repo.get("language") or "N/A"
        url = repo.get("html_url", "")

        total_stars += stars
        total_forks += forks
        total_open_issues += issues

        repo_stats.append({
            "name": name,
            "url": url,
            "stars": stars,
            "forks": forks,
            "watchers": watchers,
            "issues": issues,
            "language": language,
            "size_kb": size,
            "created": created,
            "updated": updated,
        })

    for r in repo_stats:
        lines.append(f"## {r['name']}")
        lines.append(f"URL: {r['url']}")
        lines.append(f"Stars: {r['stars']}")
        lines.append(f"Forks: {r['forks']}")
        lines.append(f"Watchers: {r['watchers']}")
        lines.append(f"Open issues: {r['issues']}")
        lines.append(f"Language: {r['language']}")
        lines.append(f"Size: {r['size_kb']} KB")
        lines.append(f"Created: {r['created']}")
        lines.append(f"Updated: {r['updated']}")
        lines.append("")

    lines.append("## Summary")
    lines.append(f"Total repos: {len(repo_stats)}")
    lines.append(f"Total stars: {total_stars}")
    lines.append(f"Total forks: {total_forks}")
    lines.append(f"Total open issues: {total_open_issues}")
    lines.append("")
    lines.append("## Top 10 by stars")
    for r in repo_stats[:10]:
        lines.append(f"{r['stars']:5d} ⭐  {r['forks']:3d} 🍴  {r['name']}")

    OUT_FILE.write_text("\n".join(lines), encoding="utf-8")
    append_history_csv(user, repo_stats)

    print(f"Saved report to: {OUT_FILE}")
    print(f"Appended history to: {OUT_DIR / f'history_{user}.csv'}")
    return True


def read_user_list(path):
    users = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                users.append(line.split()[0])  # allow comments after username
    return users


def main():
    parser = argparse.ArgumentParser(description="Collect GitHub public popularity stats")
    parser.add_argument("username", nargs="?", help="GitHub username to analyze")
    parser.add_argument("--list", "-l", metavar="FILE", help="File with usernames (one per line, # comments allowed)")
    args = parser.parse_args()

    token = load_token()
    if not token:
        print("Error: GITHUB_TOKEN not found. Set env var, ~/.github_token, or .env file", file=sys.stderr)
        sys.exit(1)

    HEADERS["Authorization"] = f"token {token}"

    users = []
    if args.list:
        users = read_user_list(args.list)
        print(f"Loaded {len(users)} usernames from {args.list}")
    elif args.username:
        users = [args.username]
    else:
        parser.print_help()
        sys.exit(1)

    success = 0
    for user in users:
        if process_user(user, token):
            success += 1

    print(f"\n{'='*50}")
    print(f"Done. Processed {success}/{len(users)} users successfully.")


if __name__ == "__main__":
    main()
