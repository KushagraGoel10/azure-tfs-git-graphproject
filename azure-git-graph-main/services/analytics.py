from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

# Add this here, before your existing functions.
REPORT_DEV_ALIASES = {
    "kushagra goel": "Kushagra Goel",
    "kushagra_rts": "Kushagra Goel",
}

def canonicalize_author(author: str, source: str) -> str:
    """
    Return the logical developer name for a contribution.

    Only merge aliases for report_dev.
    Other sources keep their original developer names.
    """
    if source != "report_dev":
        return author

    normalized_author = " ".join(author.split()).casefold()

    return REPORT_DEV_ALIASES.get(
        normalized_author,
        author.strip(),
    )

Changeset = dict[str, Any]
GroupedChangesets = dict[str, list[Changeset]]
DeveloperDateGroups = dict[str, GroupedChangesets]


from datetime import datetime

def parse_created_datetime(created_date: str) -> datetime | None:
    """Parse Azure DevOps ISO date values into datetime objects."""
    if not created_date:
        return None

    try:
        # Handle timestamps ending in Z
        if created_date.endswith("Z"):
            created_date = created_date[:-1]

        # Normalize milliseconds to exactly 6 digits (microseconds)
        if "." in created_date:
            base, fraction = created_date.split(".", 1)
            fraction = fraction.ljust(6, "0")[:6]
            created_date = f"{base}.{fraction}"

        return datetime.fromisoformat(created_date)

    except ValueError:
        return None


def parse_created_date(created_date: str) -> date | None:
    """Parse Azure DevOps ISO date values into date objects."""
    parsed_datetime = parse_created_datetime(created_date)
    if parsed_datetime is None:
        return None
    return parsed_datetime.date()


def format_time(created_date: str) -> str:
    """Return a readable 24-hour time for a changeset."""
    parsed_datetime = parse_created_datetime(created_date)
    if parsed_datetime is None:
        return "N/A"
    return parsed_datetime.strftime("%H:%M")


def extract_changesets(raw_data: dict[str, Any]) -> list[Changeset]:
    """Extract only the TFVC fields used by the dashboard."""
    values = raw_data.get("value", [])
    if not isinstance(values, list):
        return []

    changesets: list[Changeset] = []
    for item in values:
        if not isinstance(item, dict):
            continue

        author = item.get("author") or {}
        author_name = author.get("displayName") or author.get("uniqueName") or "Unknown"
        created_date = item.get("createdDate", "")
        changesets.append(
            {
                "author": author_name,
                "comment": item.get("comment", ""),
                "createdDate": created_date,
                "date": parse_created_date(created_date),
                "time": format_time(created_date),
                "changesetId": item.get("changesetId"),
            }
        )

    return changesets


def group_by_developer(changesets: list[Changeset]) -> GroupedChangesets:
    """Group changesets by developer display name."""
    grouped: defaultdict[str, list[Changeset]] = defaultdict(list)
    for changeset in changesets:
        grouped[str(changeset["author"])].append(changeset)
    return dict(grouped)


def group_by_date(changesets: list[Changeset]) -> GroupedChangesets:
    """Group changesets by ISO date."""
    grouped: defaultdict[str, list[Changeset]] = defaultdict(list)
    for changeset in changesets:
        changeset_date = changeset.get("date")
        if isinstance(changeset_date, date):
            grouped[changeset_date.isoformat()].append(changeset)
    return dict(grouped)


def group_by_developer_and_date(changesets: list[Changeset]) -> DeveloperDateGroups:
    """Group changesets by developer, then by ISO date."""
    grouped: defaultdict[str, defaultdict[str, list[Changeset]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for changeset in changesets:
        changeset_date = changeset.get("date")
        if isinstance(changeset_date, date):
            grouped[str(changeset["author"])][changeset_date.isoformat()].append(changeset)

    return {
        developer: dict(date_groups)
        for developer, date_groups in grouped.items()
    }


def calculate_streaks(active_dates: set[date]) -> tuple[int, int]:
    """Calculate current and longest daily contribution streaks."""
    if not active_dates:
        return 0, 0

    today = date.today()
    current_streak = 0
    cursor = today
    while cursor in active_dates:
        current_streak += 1
        cursor -= timedelta(days=1)

    longest_streak = 0
    running_streak = 0
    previous_date: date | None = None
    for active_date in sorted(active_dates):
        if previous_date and active_date == previous_date + timedelta(days=1):
            running_streak += 1
        else:
            running_streak = 1
        longest_streak = max(longest_streak, running_streak)
        previous_date = active_date

    return current_streak, longest_streak


def most_active_day(changesets: list[Changeset]) -> str:
    """Return the highest-contribution date and count."""
    by_date = group_by_date(changesets)
    if not by_date:
        return "N/A"

    day, day_changesets = max(by_date.items(), key=lambda item: len(item[1]))
    return f"{day} ({len(day_changesets)})"


def most_active_weekday(changesets: list[Changeset]) -> str:
    """Return the weekday with the highest total contribution count."""
    grouped: defaultdict[int, int] = defaultdict(int)
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    for changeset in changesets:
        changeset_date = changeset.get("date")
        if isinstance(changeset_date, date):
            grouped[changeset_date.weekday()] += 1

    if not grouped:
        return "N/A"

    weekday, count = max(grouped.items(), key=lambda item: item[1])
    return f"{weekday_names[weekday]} ({count})"


def most_active_month(changesets: list[Changeset]) -> str:
    """Return the highest-contribution calendar month and count."""
    grouped: defaultdict[str, int] = defaultdict(int)
    for changeset in changesets:
        changeset_date = changeset.get("date")
        if isinstance(changeset_date, date):
            grouped[changeset_date.strftime("%Y-%m")] += 1

    if not grouped:
        return "N/A"

    month, count = max(grouped.items(), key=lambda item: item[1])
    return f"{month} ({count})"


def average_contributions_per_day(changesets: list[Changeset]) -> float:
    """Calculate average contributions per active contribution day."""
    active_dates = {
        changeset["date"]
        for changeset in changesets
        if isinstance(changeset.get("date"), date)
    }
    if not active_dates:
        return 0.0
    return round(len(changesets) / len(active_dates), 2)


def build_calendar_summary(changesets: list[Changeset], heatmap_dates: list[str]) -> str:
    """Summarize contribution activity inside the visible heatmap range."""
    if not heatmap_dates:
        return "No calendar range available"

    visible_dates = set(heatmap_dates)
    contribution_dates = {
        changeset["date"].isoformat()
        for changeset in changesets
        if isinstance(changeset.get("date"), date)
        and changeset["date"].isoformat() in visible_dates
    }
    total_contributions = sum(
        1
        for changeset in changesets
        if isinstance(changeset.get("date"), date)
        and changeset["date"].isoformat() in visible_dates
    )

    return (
        f"{total_contributions} contributions across "
        f"{len(contribution_dates)} active days"
    )


def build_statistics(changesets: list[Changeset], heatmap_dates: list[str] | None = None) -> dict[str, Any]:
    """Build all developer statistics shown in the dashboard."""
    active_dates = {
        changeset["date"]
        for changeset in changesets
        if isinstance(changeset.get("date"), date)
    }
    current_streak, longest_streak = calculate_streaks(active_dates)
    calendar_dates = heatmap_dates or build_heatmap_dates()

    return {
        "selected_user_contributions": len(changesets),
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "most_active_day": most_active_day(changesets),
        "most_active_weekday": most_active_weekday(changesets),
        "most_active_month": most_active_month(changesets),
        "average_contributions_per_day": average_contributions_per_day(changesets),
        "calendar_summary": build_calendar_summary(changesets, calendar_dates),
    }


def build_developer_statistics(
    developers: list[str],
    changesets_by_developer: GroupedChangesets,
    heatmap_dates: list[str],
) -> dict[str, dict[str, Any]]:
    """Build statistics once for each developer."""
    return {
        developer: build_statistics(changesets_by_developer.get(developer, []), heatmap_dates)
        for developer in developers
    }


def build_top_contributors(
    changesets_by_developer: GroupedChangesets,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """Return the highest contributing developers for the selected source."""
    ranked_contributors = sorted(
        (
            {
                "developer": developer,
                "contributions": len(changesets),
            }
            for developer, changesets in changesets_by_developer.items()
            if changesets
        ),
        key=lambda item: (-item["contributions"], item["developer"].lower(), item["developer"]),
    )
    return ranked_contributors[:limit]


def build_contribution_years(changesets: list[Changeset]) -> list[int]:
    """Return contribution years available for the selected source."""
    return sorted(
        {
            changeset_date.year
            for changeset in changesets
            if isinstance((changeset_date := changeset.get("date")), date)
        },
        reverse=True,
    )


def build_top_contributors_by_year(
    changesets_by_developer: GroupedChangesets,
    years: list[int],
) -> dict[str, list[dict[str, Any]]]:
    """Build top contributor rankings for each available contribution year."""
    top_contributors_by_year: dict[str, list[dict[str, Any]]] = {}

    for year in years:
        yearly_changesets_by_developer: GroupedChangesets = {
            developer: [
                changeset
                for changeset in changesets
                if isinstance(changeset.get("date"), date)
                and changeset["date"].year == year
            ]
            for developer, changesets in changesets_by_developer.items()
        }
        top_contributors_by_year[str(year)] = build_top_contributors(
            yearly_changesets_by_developer
        )

    return top_contributors_by_year


def build_universal_top_contributors_by_year(
    application_changesets: list[Changeset],
    reports_changesets: list[Changeset],
    limit: int = 3,
) -> dict[str, list[dict[str, Any]]]:
    """
    Build yearly top contributors across Application + Reports combined.
    Report aliases are already canonicalized before this function is called.
    """
    combined_changesets = application_changesets + reports_changesets

    years = sorted(
        {
            changeset_date.year
            for changeset in combined_changesets
            if isinstance(
                (changeset_date := changeset.get("date")),
                date,
            )
        },
        reverse=True,
    )

    universal_top_contributors_by_year: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for year in years:
        yearly_changesets_by_developer: GroupedChangesets = defaultdict(list)

        for changeset in combined_changesets:
            changeset_date = changeset.get("date")

            if (
                isinstance(changeset_date, date)
                and changeset_date.year == year
            ):
                yearly_changesets_by_developer[
                    str(changeset["author"])
                ].append(changeset)

        universal_top_contributors_by_year[str(year)] = build_top_contributors(
            dict(yearly_changesets_by_developer),
            limit=limit,
        )

    return universal_top_contributors_by_year


def prepare_universal_top_contributors_data(
    application_raw_data: dict[str, Any],
    reports_raw_data: dict[str, Any],
    limit: int = 3,
) -> dict[str, Any]:
    """
    Prepare universal top contributors using all Application and Reports
    changesets while preserving the existing dashboard structure.
    """
    application_changesets = extract_changesets(application_raw_data)
    reports_changesets = extract_changesets(reports_raw_data)

    # Apply the same alias normalization used by the report dashboard.
    for changeset in application_changesets:
        changeset["author"] = canonicalize_author(
            str(changeset["author"]),
            "application",
        )

    for changeset in reports_changesets:
        changeset["author"] = canonicalize_author(
            str(changeset["author"]),
            "report_dev",
        )

    top_contributors_by_year = build_universal_top_contributors_by_year(
        application_changesets,
        reports_changesets,
        limit=limit,
    )

    years = sorted(
        {
            changeset_date.year
            for changeset in application_changesets + reports_changesets
            if isinstance(
                (changeset_date := changeset.get("date")),
                date,
            )
        },
        reverse=True,
    )

    selected_year = resolve_default_top_contributor_year(years)

    return {
        "top_contributors": top_contributors_by_year.get(
            selected_year,
            [],
        ),
        "selected_top_contributor_year": selected_year,
        "top_contributor_years": years,
        "top_contributors_by_year": top_contributors_by_year,
    }

def resolve_default_top_contributor_year(years: list[int]) -> str:
    """Default the top contributor filter to the current year when available."""
    current_year = date.today().year
    if current_year in years:
        return str(current_year)
    if years:
        return str(years[0])
    return ""


def build_contribution_counts_by_developer_and_date(
    changesets_by_developer_and_date: DeveloperDateGroups,
) -> dict[str, dict[str, int]]:
    """Build compact contribution counts for heatmap rendering."""
    return {
        developer: {
            changeset_date: len(changesets)
            for changeset_date, changesets in date_groups.items()
        }
        for developer, date_groups in changesets_by_developer_and_date.items()
    }


def build_changeset_details_by_developer_and_date(
    changesets_by_developer_and_date: DeveloperDateGroups,
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    """Build JSON-safe changeset details for the clicked-day panel."""
    return {
        developer: {
            changeset_date: [
                {
                    "changesetId": changeset.get("changesetId"),
                    "comment": changeset.get("comment") or "No comment",
                    "time": changeset.get("time") or "N/A",
                }
                for changeset in sorted(
                    changesets,
                    key=lambda item: str(item.get("createdDate", "")),
                    reverse=True,
                )
            ]
            for changeset_date, changesets in date_groups.items()
        }
        for developer, date_groups in changesets_by_developer_and_date.items()
    }


def build_heatmap_dates(days: int = 365) -> list[str]:
    """Return ISO dates for the visible contribution calendar range."""
    today = date.today()
    start_date = today - timedelta(days=days - 1)
    return [
        (start_date + timedelta(days=offset)).isoformat()
        for offset in range(days)
    ]


def build_empty_dashboard_data() -> dict[str, Any]:
    """Return a complete empty dashboard payload."""
    heatmap_dates = build_heatmap_dates()
    return {
        "developers": [],
        "selected_developer": "",
        "total_project_changesets": 0,
        "statistics": build_statistics([], heatmap_dates),
        "developer_statistics": {},
        "top_contributors": [],
        "selected_top_contributor_year": "",
        "top_contributor_years": [],
        "top_contributors_by_year": {},
        "contribution_counts_by_developer_and_date": {},
        "changeset_details_by_developer_and_date": {},
        "heatmap_dates": heatmap_dates,
    }


def prepare_dashboard_data(
    raw_data: dict[str, Any],
    selected_developer: str | None = None,
    source: str = "application",
) -> dict[str, Any]:
    """Prepare all dashboard data, merging report_dev aliases."""

    heatmap_dates = build_heatmap_dates()
    changesets = extract_changesets(raw_data)

    # Merge duplicate Azure DevOps identities.
    for changeset in changesets:
        changeset["author"] = canonicalize_author(
            str(changeset["author"]),
            source,
        )

    print("Total extracted:", len(changesets))

    developers = sorted({
        str(changeset["author"])
        for changeset in changesets
    })

    resolved_developer = (
    selected_developer
    if selected_developer in developers
    else ""
    )

    changesets_by_developer = group_by_developer(changesets)

    changesets_by_developer_and_date = (
        group_by_developer_and_date(changesets)
    )

    selected_changesets = changesets_by_developer.get(
        resolved_developer,
        [],
    )

    developer_statistics = build_developer_statistics(
        developers,
        changesets_by_developer,
        heatmap_dates,
    )

    top_contributor_years = build_contribution_years(changesets)

    selected_top_contributor_year = (
        resolve_default_top_contributor_year(
            top_contributor_years
        )
    )

    top_contributors_by_year = build_top_contributors_by_year(
        changesets_by_developer,
        top_contributor_years,
    )

    return {
        "developers": developers,
        "selected_developer": resolved_developer,
        "total_project_changesets": len(changesets),
        "statistics": build_statistics(
            selected_changesets,
            heatmap_dates,
        ),
        "developer_statistics": developer_statistics,
        "top_contributors": top_contributors_by_year.get(
            selected_top_contributor_year,
            [],
        ),
        "selected_top_contributor_year": selected_top_contributor_year,
        "top_contributor_years": top_contributor_years,
        "top_contributors_by_year": top_contributors_by_year,
        "contribution_counts_by_developer_and_date": (
            build_contribution_counts_by_developer_and_date(
                changesets_by_developer_and_date
            )
        ),
        "changeset_details_by_developer_and_date": (
            build_changeset_details_by_developer_and_date(
                changesets_by_developer_and_date
            )
        ),
        "heatmap_dates": heatmap_dates,
    }