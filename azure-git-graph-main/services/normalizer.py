from __future__ import annotations

from typing import Any


def normalize_tfvc(raw_data: dict[str, Any]) -> dict[str, Any]:
    """
    TFVC already returns the format expected by analytics.
    """
    return raw_data


def normalize_git(raw_data: dict[str, Any]) -> dict[str, Any]:
    """
    Convert Git commits API response into the TFVC format
    expected by analytics.py.
    """

    commits = []

    for item in raw_data.get("value", []):

        author = item.get("author", {})

        commits.append(
            {
                "changesetId": item.get("commitId"),
                "comment": item.get("comment", ""),
                "createdDate": author.get("date", ""),
                "author": {
                    "displayName": author.get("name", "Unknown")
                }
            }
        )

    return {
        "count": len(commits),
        "value": commits
    }