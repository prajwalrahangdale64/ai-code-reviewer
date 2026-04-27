import re
import requests
import os
from dotenv import load_dotenv

load_dotenv()

SUPPORTED_EXTENSIONS = [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rb", ".cs"]


def parse_pr_url(url: str):
    """Extract owner, repo, and PR number from a GitHub PR URL."""
    pattern = r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.match(pattern, url.strip())
    if not match:
        raise ValueError("Invalid GitHub PR URL. Expected format: https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), int(match.group(3))


def fetch_pr_code(pr_url: str) -> str:
    """
    Fetches the full file contents of all changed code files in a GitHub PR.
    Returns a single combined string ready to pass into review_code().
    Uses GITHUB_TOKEN from .env if available (required for private repos).
    """
    owner, repo, pr_number = parse_pr_url(pr_url)

    token = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Step 1: Get list of files changed in the PR
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files"
    response = requests.get(api_url, headers=headers)

    if response.status_code == 404:
        raise ValueError("PR not found. Check the URL or make sure the repo is public.")
    elif response.status_code == 403:
        raise ValueError("Access denied. Add a GITHUB_TOKEN in your .env for private repos.")
    response.raise_for_status()

    files = response.json()

    # Step 2: Fetch full content of each supported code file
    combined_code = []
    for file in files:
        filename = file["filename"]
        if not any(filename.endswith(ext) for ext in SUPPORTED_EXTENSIONS):
            continue

        raw_url = file.get("raw_url")
        if not raw_url:
            continue

        raw_response = requests.get(raw_url, headers=headers)
        if raw_response.status_code == 200:
            combined_code.append(f"# ── File: {filename} ──\n{raw_response.text}")

    if not combined_code:
        raise ValueError("No supported code files found in this PR (.py, .js, .ts, etc.)")

    return "\n\n".join(combined_code)