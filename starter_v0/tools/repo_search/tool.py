from __future__ import annotations

from typing import Any
import requests


def search_github_repos(
    query: str,
    language: str | None = None,
    sort: str = "stars",
    limit: int = 5,
) -> dict[str, Any]:
    """Search GitHub repositories for open-source AI and software projects."""
    if not query or not query.strip():
        return {"error": "ValueError", "message": "query parameter cannot be empty"}

    search_q = query.strip()
    if language:
        search_q += f" language:{language.strip()}"

    url = f"https://api.github.com/search/repositories?q={search_q}&sort={sort}&order=desc&per_page={limit}"
    headers = {"User-Agent": "AI20k-Day04-Research-Agent/1.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return {
                "error": "APIError",
                "message": f"GitHub API error {resp.status_code}: {resp.text[:200]}",
                "items": [],
            }
        data = resp.json()
        items = []
        for item in data.get("items", []):
            items.append({
                "name": item.get("full_name", ""),
                "description": item.get("description", ""),
                "stars": item.get("stargazers_count", 0),
                "url": item.get("html_url", ""),
                "language": item.get("language", ""),
            })
        return {"error": None, "message": None, "item_count": len(items), "items": items}
    except Exception as exc:
        return {"error": type(exc).__name__, "message": str(exc), "items": []}
