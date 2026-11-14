#!/usr/bin/env python3
"""
Offline Repository Snapshot Fetcher for Jezali Portfolio
Fetches public repositories from GitHub API and writes repos.json for offline build fallback.
"""

import urllib.request
import json
import sys

GITHUB_USER = "Jezali"
API_URL = f"https://api.github.com/users/{GITHUB_USER}/repos?per_page=100&sort=updated"
OUTPUT_FILE = "repos.json"

def fetch_repos():
    req = urllib.request.Request(
        API_URL,
        headers={"User-Agent": "Jezali-Portfolio-Snapshot-Builder"}
    )
    try:
        print(f"Fetching repos for {GITHUB_USER} from {API_URL}...")
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                print(f"Successfully saved {len(data)} repositories to {OUTPUT_FILE}")
            else:
                print(f"Failed with HTTP status: {response.status}", file=sys.stderr)
                sys.exit(1)
    except Exception as e:
        print(f"Error fetching repositories: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    fetch_repos()
