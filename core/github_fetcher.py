import re
import requests
import os
from dotenv import load_dotenv

load_dotenv()

SUPPORTED_EXTENSIONS = [".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rb", ".cs"]


# ── Helpers ────────────────────────────────────────────────────────────────────

def parse_pr_url(url: str):
    """Extract owner, repo, and PR number from a GitHub PR URL."""
    pattern = r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.match(pattern, url.strip())
    if not match:
        raise ValueError(
            "Invalid GitHub PR URL. Expected format: https://github.com/owner/repo/pull/123"
        )
    return match.group(1), match.group(2), int(match.group(3))


def _build_headers() -> dict:
    token = os.getenv("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _check_response(response: requests.Response) -> None:
    if response.status_code == 404:
        raise ValueError("PR not found. Check the URL or make sure the repo is public.")
    if response.status_code == 403:
        raise ValueError("Access denied. Add a GITHUB_TOKEN in your .env for private repos.")
    response.raise_for_status()


# ── New: PR metadata + file list ───────────────────────────────────────────────

def fetch_pr_info(pr_url: str) -> dict:
    """
    Fetches PR metadata and the list of changed files.

    Returns:
        {
            "title":         str,
            "source_branch": str,
            "base_branch":   str,
            "changed_files": [{"filename": str, "raw_url": str, "status": str}, ...]
        }
    Only files whose extension is in SUPPORTED_EXTENSIONS are included.
    """
    owner, repo, pr_number = parse_pr_url(pr_url)
    headers = _build_headers()

    # PR metadata (title, branches)
    pr_resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}",
        headers=headers,
    )
    _check_response(pr_resp)
    pr_data = pr_resp.json()

    # Changed files
    files_resp = requests.get(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}/files",
        headers=headers,
    )
    _check_response(files_resp)

    changed_files = [
        {
            "filename": f["filename"],
            "raw_url":  f.get("raw_url"),
            "status":   f.get("status", "modified"),
        }
        for f in files_resp.json()
        if any(f["filename"].endswith(ext) for ext in SUPPORTED_EXTENSIONS)
    ]

    return {
        "title":         pr_data["title"],
        "source_branch": pr_data["head"]["ref"],
        "base_branch":   pr_data["base"]["ref"],
        "changed_files": changed_files,
    }


# ── New: single-file fetch ─────────────────────────────────────────────────────

def fetch_file_content(raw_url: str) -> str:
    """Fetches the raw text content of a single file by its raw_url."""
    headers = _build_headers()
    resp = requests.get(raw_url, headers=headers)
    if resp.status_code != 200:
        raise ValueError(f"Could not fetch file (HTTP {resp.status_code}).")
    return resp.text


# ── Legacy: fetch all files at once (kept for backwards compatibility) ─────────

def fetch_pr_code(pr_url: str) -> str:
    """
    Fetches the full content of all changed code files in a PR and
    returns them as a single combined string.
    """
    pr_info = fetch_pr_info(pr_url)
    if not pr_info["changed_files"]:
        raise ValueError("No supported code files found in this PR (.py, .js, .ts, etc.)")

    parts = []
    for f in pr_info["changed_files"]:
        if f["raw_url"]:
            content = fetch_file_content(f["raw_url"])
            parts.append(f"# ── File: {f['filename']} ──\n{content}")

    return "\n\n".join(parts)