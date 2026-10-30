from __future__ import annotations

from typing import Any

import requests
from requests import RequestException
from requests_negotiate_sspi import HttpNegotiateAuth

from services.normalizer import normalize_tfvc, normalize_git


APPLICATION_URL = (
    "http://10.64.33.98:8080/tfs/SLAM_APPLICATION/SLAM_PROD/"
    "_apis/tfvc/changesets?$top=10000&api-version=5.0"
)

REPORT_DEV_URL = (
    "http://10.64.33.98:8080/tfs/SLAMREPORTS_LIVE_REPO/SLAMREPORTS/"
    "_apis/git/repositories/SLAMREPORTS/"
    "commits?searchCriteria.itemVersion.version=SLAMREPORTS_DEV"
    "&searchCriteria.$top=10000&api-version=5.0"
)

REPORT_TEST_URL = (
    "http://10.64.33.98:8080/tfs/SLAMREPORTS_LIVE_REPO/SLAMREPORTS/"
    "_apis/git/repositories/SLAMREPORTS/"
    "commits?searchCriteria.itemVersion.version=SLAMREPORTS_TEST"
    "&searchCriteria.$top=10000&api-version=5.0"
)

REPORT_MASTER_URL = (
    "http://10.64.33.98:8080/tfs/SLAMREPORTS_LIVE_REPO/SLAMREPORTS/"
    "_apis/git/repositories/SLAMREPORTS/"
    "commits?searchCriteria.itemVersion.version=master"
    "&searchCriteria.$top=10000&api-version=5.0"
)


URLS = {
    "application": APPLICATION_URL,
    "report_dev": REPORT_DEV_URL,
    "report_test": REPORT_TEST_URL,
    "report_master": REPORT_MASTER_URL,
}


def get_repository_data(source: str) -> dict[str, Any]:
    try:
        response = requests.get(
            URLS[source],
            auth=HttpNegotiateAuth(),
            timeout=30,
        )
    except RequestException as exc:
        raise RuntimeError(
            "Unable to connect to the Azure DevOps TFVC API. "
            "Check that the TFS server is reachable from this machine "
            "and try again."
        ) from exc

    if response.status_code != 200:
        response_preview = " ".join(response.text.split())[:300]

        if response.status_code == 401:
            raise RuntimeError(
                "Azure DevOps TFVC API returned 401. The app attempted "
                "Windows integrated authentication, but Azure DevOps Server "
                "still rejected the request. Make sure you are running Flask "
                "as a Windows user that has access to this TFS project."
            )

        raise RuntimeError(
            "Azure DevOps TFVC API returned "
            f"{response.status_code}: {response_preview}"
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Azure DevOps TFVC API returned invalid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise RuntimeError(
            "Azure DevOps TFVC API returned an unexpected response."
        )

    value = data.get("value")

    if value is None:
        raise RuntimeError(
            "Azure DevOps TFVC API response is missing 'value'."
        )

    if not isinstance(value, list):
        raise RuntimeError(
            "Azure DevOps TFVC API response 'value' must be a list."
        )

    if source == "application":
        return normalize_tfvc(data)

    return normalize_git(data)


def get_report_commit_changes(commit_id: str) -> dict[str, Any]:
    """
    Return file changes for a SLAMREPORTS Git commit.

    Used only when the user expands a Reports changeset.
    """

    if not commit_id:
        raise RuntimeError("Commit ID is required.")

    url = (
        "http://10.64.33.98:8080/tfs/SLAMREPORTS_LIVE_REPO/SLAMREPORTS/"
        f"_apis/git/repositories/SLAMREPORTS/commits/{commit_id}/changes"
        "?api-version=5.0"
    )

    try:
        response = requests.get(
            url,
            auth=HttpNegotiateAuth(),
            timeout=30,
        )
    except RequestException as exc:
        raise RuntimeError(
            "Unable to connect to Azure DevOps while retrieving "
            "commit changes."
        ) from exc

    if response.status_code != 200:
        response_preview = " ".join(response.text.split())[:300]

        raise RuntimeError(
            "Azure DevOps Git changes API returned "
            f"{response.status_code}: {response_preview}"
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "Azure DevOps Git changes API returned invalid JSON."
        ) from exc

    if not isinstance(data, dict):
        raise RuntimeError(
            "Azure DevOps Git changes API returned an unexpected response."
        )

    values = data.get("changes", [])

    if not isinstance(values, list):
        values = []

    files: list[dict[str, str]] = []

    added = 0
    modified = 0
    deleted = 0
    renamed = 0

    for change in values:
        if not isinstance(change, dict):
            continue

        change_type = str(
            change.get("changeType", "")
        ).lower()

        item = change.get("item") or {}

        if isinstance(item, dict):
            path = item.get("path")
        else:
            path = None

        if not path:
            path = "Unknown file"

        if "rename" in change_type:
            renamed += 1
            display_type = "Renamed"

        elif "add" in change_type:
            added += 1
            display_type = "Added"

        elif "delete" in change_type:
            deleted += 1
            display_type = "Deleted"

        elif "edit" in change_type:
            modified += 1
            display_type = "Modified"

        else:
            modified += 1
            display_type = str(
                change.get("changeType", "Changed")
            )

        files.append(
            {
                "path": str(path),
                "changeType": display_type,
            }
        )

    return {
        "total": len(files),
        "added": added,
        "modified": modified,
        "deleted": deleted,
        "renamed": renamed,
        "files": files,
    }
