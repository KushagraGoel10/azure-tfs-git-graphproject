from __future__ import annotations

from typing import Any

from flask import Flask, render_template, request

from services.analytics import (build_empty_dashboard_data, prepare_dashboard_data, prepare_universal_top_contributors_data,)
from services.tfvc import get_repository_data

from services.tfvc import ( get_repository_data, get_report_commit_changes,)

app = Flask(__name__)
_dashboard_cache: dict[str, dict[str, Any]] = {}
_universal_top_contributors_cache: dict[str, Any] | None = None


def build_empty_user_contribution_totals() -> dict[str, int]:
    """Return an empty per-user cross-project contribution summary."""
    return {
        "application": 0,
        "reports": 0,
        "total": 0,
    }


def get_dashboard_data(source: str) -> dict[str, Any]:
    global _dashboard_cache

    if source not in _dashboard_cache:
        raw_data = get_repository_data(source)
        # _dashboard_cache[source] = prepare_dashboard_data(raw_data)

        _dashboard_cache[source] = prepare_dashboard_data(
    raw_data,
    source=source,
)

    return _dashboard_cache[source]

def get_universal_top_contributors_data() -> dict[str, Any]:
    """
    Return top contributors across Application + Reports combined.
    """
    global _universal_top_contributors_cache

    if _universal_top_contributors_cache is None:
        application_raw_data = get_repository_data("application")
        reports_raw_data = get_repository_data("report_dev")

        _universal_top_contributors_cache = (
            prepare_universal_top_contributors_data(
                application_raw_data,
                reports_raw_data,
                limit=5,
            )
        )

    return _universal_top_contributors_cache


def get_user_contribution_totals_by_developer() -> dict[str, dict[str, int]]:
    """Return Application plus Report Dev contribution counts by developer."""
    application_data = get_dashboard_data("application")
    reports_data = get_dashboard_data("report_dev")
    application_statistics = application_data["developer_statistics"]
    reports_statistics = reports_data["developer_statistics"]
    developers = set(application_statistics) | set(reports_statistics)

    return {
        developer: {
            "application": application_statistics.get(developer, {}).get(
                "selected_user_contributions",
                0,
            ),
            "reports": reports_statistics.get(developer, {}).get(
                "selected_user_contributions",
                0,
            ),
            "total": (
                application_statistics.get(developer, {}).get(
                    "selected_user_contributions",
                    0,
                )
                + reports_statistics.get(developer, {}).get(
                    "selected_user_contributions",
                    0,
                )
            ),
        }
        for developer in developers
    }


@app.route("/")
def index() -> str:
    """Render the dashboard page."""
    error_message = ""
    dashboard_data = build_empty_dashboard_data()
    user_contribution_totals_by_developer: dict[str, dict[str, int]] = {}
    source = request.args.get("source", "application")

    try:
            dashboard_data = get_dashboard_data(source)

            user_contribution_totals_by_developer = (get_user_contribution_totals_by_developer())

            universal_top_contributors_data = (
                get_universal_top_contributors_data()
            )

            dashboard_data.update(universal_top_contributors_data)
    except RuntimeError as exc:
        error_message = str(exc)

    requested_developer = request.args.get("developer")
    developers = dashboard_data["developers"]
    selected_developer = (
        requested_developer
        if requested_developer in developers
        else dashboard_data["selected_developer"]
    )
    selected_user_contribution_totals = user_contribution_totals_by_developer.get(
        selected_developer,
        build_empty_user_contribution_totals(),
    )

    return render_template(
        "index.html",
        error_message=error_message,
        source=source,
        selected_developer=selected_developer,
        selected_user_contribution_totals=selected_user_contribution_totals,
        user_contribution_totals_by_developer=user_contribution_totals_by_developer,
        **{
            key: value
            for key, value in dashboard_data.items()
            if key != "selected_developer"
        },
    )

@app.route("/api/report-commit/<commit_id>/changes")
def report_commit_changes(commit_id: str):
    """Return changed files for a Reports Git commit."""

    try:
        return get_report_commit_changes(commit_id)
    except RuntimeError as exc:
        return {
            "error": str(exc)
        }, 500



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)