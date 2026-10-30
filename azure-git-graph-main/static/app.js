const dashboardDataNode = document.getElementById("dashboardData");
const dashboardData = dashboardDataNode ? JSON.parse(dashboardDataNode.textContent) : {};

const developerSelect = document.getElementById("developer");
const selectedDeveloperLabel = document.getElementById("selectedDeveloperLabel");
const heatmapGrid = document.getElementById("heatmapGrid");
const monthLabels = document.getElementById("monthLabels");
const tooltip = document.getElementById("heatmapTooltip");
const statNodes = document.querySelectorAll("[data-stat]");
const userContributionsTotal = document.getElementById("userContributionsTotal");
const userContributionsBreakdown = document.getElementById("userContributionsBreakdown");
const topContributorYear = document.getElementById("topContributorYear");
const topContributorsList = document.getElementById("topContributorsList");
const topContributorsEmptyTemplate = document.getElementById("topContributorsEmptyTemplate");
const detailsSubtitle = document.getElementById("detailsSubtitle");
const detailsCount = document.getElementById("detailsCount");
const detailsEmptyState = document.getElementById("detailsEmptyState");
const changesetList = document.getElementById("changesetList");
const loadingSpinner = document.getElementById("loadingSpinner");
const monthNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

let selectedCell = null;

function parseIsoDate(value) {
    const parts = value.split("-").map(Number);
    return new Date(parts[0], parts[1] - 1, parts[2]);
}

function formatDisplayDate(value) {
    const parsed = parseIsoDate(value);
    return `${parsed.getDate()} ${monthNames[parsed.getMonth()]} ${parsed.getFullYear()}`;
}

function getContributionLevel(count) {
    if (count === 0) {
        return 0;
    }
    if (count === 1) {
        return 1;
    }
    if (count <= 3) {
        return 2;
    }
    if (count <= 6) {
        return 3;
    }
    return 4;
}

function buildHeatmapDays() {
    if (!dashboardData.heatmapDates || dashboardData.heatmapDates.length === 0) {
        return [];
    }

    const firstDate = parseIsoDate(dashboardData.heatmapDates[0]);
    const leadingEmptyDays = firstDate.getDay();
    const cells = [];

    for (let index = 0; index < leadingEmptyDays; index += 1) {
        cells.push(null);
    }

    dashboardData.heatmapDates.forEach((dateValue) => cells.push(dateValue));
    return cells;
}

function renderMonthLabels(cells) {
    monthLabels.innerHTML = "";
    let previousMonth = "";

    cells.forEach((dateValue, index) => {
        if (index % 7 !== 0) {
            return;
        }

        const label = document.createElement("span");
        label.className = "month-label";
        if (dateValue) {
            const parsed = parseIsoDate(dateValue);
            const currentMonth = `${parsed.getFullYear()}-${parsed.getMonth()}`;
            if (currentMonth !== previousMonth) {
                label.textContent = monthNames[parsed.getMonth()];
                previousMonth = currentMonth;
            }
        }
        monthLabels.appendChild(label);
    });
}

function showLoading() {
    loadingSpinner.classList.add("is-visible");
}

function hideLoading() {
    window.setTimeout(() => {
        loadingSpinner.classList.remove("is-visible");
    }, 180);
}

function clearDetails(developer) {
    changesetList.innerHTML = "";
    detailsSubtitle.textContent = developer ? "Select a heatmap square to inspect a day" : "No developer selected";
    detailsCount.textContent = "0 changesets";
    detailsEmptyState.textContent = "Click a contribution square to see changeset IDs, comments, and times for that day.";
    detailsEmptyState.hidden = false;
    selectedCell = null;
}

// function renderDetails(developer, dateValue, cell) {
//     const detailsByDate = dashboardData.changesetDetails[developer] || {};
//     const changesets = detailsByDate[dateValue] || [];

//     if (selectedCell) {
//         selectedCell.classList.remove("is-selected");
//     }
//     selectedCell = cell;
//     selectedCell.classList.add("is-selected");

//     detailsSubtitle.textContent = formatDisplayDate(dateValue);
//     detailsCount.textContent = `${changesets.length} changeset${changesets.length === 1 ? "" : "s"}`;
//     changesetList.innerHTML = "";

//     if (changesets.length === 0) {
//         detailsEmptyState.hidden = false;
//         detailsEmptyState.textContent = "No changesets were found for this day.";
//         return;
//     }

//     detailsEmptyState.hidden = true;
//     changesets.forEach((changeset) => {
//         const row = document.createElement("article");
//         row.className = "changeset-row";

//         const id = document.createElement("div");
//         id.className = "changeset-id";
//         id.textContent = changeset.changesetId || "N/A";

//         const comment = document.createElement("div");
//         comment.className = "changeset-comment";
//         comment.textContent = changeset.comment || "No comment";

//         const time = document.createElement("div");
//         time.className = "changeset-time";
//         time.textContent = changeset.time || "N/A";

//         row.append(id, comment, time);
//         changesetList.appendChild(row);
//     });
// }

async function loadReportCommitChanges(commitId, container) {
    if (!commitId || !container) {
        return;
    }

    container.innerHTML = `
        <div class="commit-files-loading">
            Loading changed files...
        </div>
    `;

    try {
        const response = await fetch(
            `/api/report-commit/${encodeURIComponent(commitId)}/changes`
        );

        const data = await response.json();

        if (!response.ok || data.error) {
            throw new Error(data.error || "Unable to load changed files.");
        }

        container.innerHTML = "";

        const summary = document.createElement("div");
        summary.className = "commit-files-summary";

        const total = document.createElement("strong");
        total.textContent = `${data.total} file${data.total === 1 ? "" : "s"} changed`;

        summary.appendChild(total);

        if (data.added > 0) {
            const added = document.createElement("span");
            added.className = "file-change-added";
            added.textContent = `${data.added} Added`;
            summary.appendChild(added);
        }

        if (data.modified > 0) {
            const modified = document.createElement("span");
            modified.className = "file-change-modified";
            modified.textContent = `${data.modified} Modified`;
            summary.appendChild(modified);
        }

        if (data.deleted > 0) {
            const deleted = document.createElement("span");
            deleted.className = "file-change-deleted";
            deleted.textContent = `${data.deleted} Deleted`;
            summary.appendChild(deleted);
        }

        if (data.renamed > 0) {
            const renamed = document.createElement("span");
            renamed.className = "file-change-renamed";
            renamed.textContent = `${data.renamed} Renamed`;
            summary.appendChild(renamed);
        }

        container.appendChild(summary);

        const fileList = document.createElement("div");
        fileList.className = "commit-files-list";

        data.files.forEach((file) => {
            const fileRow = document.createElement("div");
            fileRow.className = "commit-file-row";

            const type = document.createElement("span");
            type.className = "commit-file-type";
            type.textContent = file.changeType;

            const path = document.createElement("span");
            path.className = "commit-file-path";
            path.textContent = file.path;

            fileRow.append(type, path);
            fileList.appendChild(fileRow);
        });

        container.appendChild(fileList);

    } catch (error) {
        container.innerHTML = `
            <div class="commit-files-error">
                Unable to load changed files.
            </div>
        `;

        console.error(error);
    }
}


function renderDetails(developer, dateValue, cell) {
    const detailsByDate = dashboardData.changesetDetails[developer] || {};
    const changesets = detailsByDate[dateValue] || [];

    if (selectedCell) {
        selectedCell.classList.remove("is-selected");
    }

    selectedCell = cell;
    selectedCell.classList.add("is-selected");

    detailsSubtitle.textContent = formatDisplayDate(dateValue);

    detailsCount.textContent =
        `${changesets.length} changeset${changesets.length === 1 ? "" : "s"}`;

    changesetList.innerHTML = "";

    if (changesets.length === 0) {
        detailsEmptyState.hidden = false;
        detailsEmptyState.textContent = "No changesets were found for this day.";
        return;
    }

    detailsEmptyState.hidden = true;

    changesets.forEach((changeset) => {
        const row = document.createElement("article");
        row.className = "changeset-row";

        /*
         * LEFT
         * Commit ID
         */
        const id = document.createElement("div");
        id.className = "changeset-id";
        id.textContent = changeset.changesetId || "N/A";

        /*
         * MIDDLE
         * Commit comment + files
         */
        const content = document.createElement("div");
        content.className = "changeset-content";

        const comment = document.createElement("div");
        comment.className = "changeset-comment";
        comment.textContent = changeset.comment || "No comment";

        content.appendChild(comment);

        /*
         * Reports only
         */
        if (dashboardData.source === "report_dev") {
            const filesContainer = document.createElement("div");
            filesContainer.className = "commit-files-container";

            const viewFilesButton = document.createElement("button");
            viewFilesButton.type = "button";
            viewFilesButton.className = "view-files-button";
            viewFilesButton.textContent = "View changed files";

            viewFilesButton.addEventListener("click", async () => {
                viewFilesButton.disabled = true;
                viewFilesButton.textContent = "Loading...";

                await loadReportCommitChanges(
                    changeset.changesetId,
                    filesContainer
                );

                viewFilesButton.remove();
            });

            content.appendChild(viewFilesButton);
            content.appendChild(filesContainer);
        }

        /*
         * RIGHT
         * Time
         */
        const time = document.createElement("div");
        time.className = "changeset-time";
        time.textContent = changeset.time || "N/A";

        row.append(id, content, time);

        changesetList.appendChild(row);
    });
}

function renderHeatmap(developer) {
    const counts = dashboardData.contributionCounts[developer] || {};
    const cells = buildHeatmapDays();
    heatmapGrid.innerHTML = "";
    heatmapGrid.style.gridTemplateColumns = `repeat(${Math.ceil(cells.length / 7)}, 12px)`;
    monthLabels.style.gridTemplateColumns = heatmapGrid.style.gridTemplateColumns;
    renderMonthLabels(cells);

    cells.forEach((dateValue) => {
        const cell = document.createElement("button");
        cell.type = "button";
        cell.className = "heatmap-cell";

        if (!dateValue) {
            cell.classList.add("is-empty");
            cell.setAttribute("tabindex", "-1");
            heatmapGrid.appendChild(cell);
            return;
        }

        const count = counts[dateValue] || 0;
        cell.classList.add(`level-${getContributionLevel(count)}`);
        cell.setAttribute("aria-label", `${formatDisplayDate(dateValue)}: ${count} Contributions`);
        cell.dataset.date = dateValue;
        cell.dataset.count = String(count);

        cell.addEventListener("mouseenter", showTooltip);
        cell.addEventListener("mousemove", moveTooltip);
        cell.addEventListener("mouseleave", hideTooltip);
        cell.addEventListener("focus", showTooltip);
        cell.addEventListener("blur", hideTooltip);
        cell.addEventListener("click", () => renderDetails(developer, dateValue, cell));

        heatmapGrid.appendChild(cell);
    });
}

function updateStatistics(developer) {
    const stats = dashboardData.developerStatistics[developer] || {
        selected_user_contributions: 0,
        current_streak: 0,
        longest_streak: 0,
        most_active_day: "N/A",
        most_active_weekday: "N/A",
        most_active_month: "N/A",
        average_contributions_per_day: 0,
        calendar_summary: "0 contributions across 0 active days"
    };

    selectedDeveloperLabel.textContent = developer || "No developer selected";
    statNodes.forEach((node) => {
        const key = node.dataset.stat;
        node.textContent = stats[key];
    });
}

function updateUserContributionTotals(developer) {
    const totals = (dashboardData.userContributionTotals || {})[developer] || {
        application: 0,
        reports: 0,
        total: 0
    };

    if (userContributionsTotal) {
        userContributionsTotal.textContent = totals.total;
    }

    if (userContributionsBreakdown) {
        userContributionsBreakdown.textContent = `Application ${totals.application} - Reports ${totals.reports}`;
    }
}

function getTopContributorsForYear(year) {
    return (dashboardData.topContributorsByYear || {})[year] || [];
}

function renderTopContributors(year) {
    if (!topContributorsList) {
        return;
    }

    const contributors = getTopContributorsForYear(year);
    topContributorsList.innerHTML = "";

    if (contributors.length === 0) {
        if (topContributorsEmptyTemplate) {
            topContributorsList.appendChild(topContributorsEmptyTemplate.content.cloneNode(true));
        }
        return;
    }

    contributors.forEach((contributor, index) => {
        const row = document.createElement("article");
        row.className = `top-contributor-row rank-${index + 1}`;

        const rank = document.createElement("div");
        rank.className = "top-contributor-rank";
        rank.setAttribute("aria-label", `Rank ${index + 1}`);
        rank.textContent = String(index + 1);

        const name = document.createElement("div");
        name.className = "top-contributor-name";
        name.textContent = contributor.developer || "Unknown";

        const count = document.createElement("div");
        count.className = "top-contributor-count";

        const total = document.createElement("strong");
        total.textContent = String(contributor.contributions || 0);

        const label = document.createElement("span");
        label.textContent = contributor.contributions === 1 ? "contribution" : "contributions";

        count.append(total, label);
        row.append(rank, name, count);
        topContributorsList.appendChild(row);
    });
}

function showTooltip(event) {
    const target = event.currentTarget;
    tooltip.innerHTML = `<strong>${formatDisplayDate(target.dataset.date)}</strong><br>${target.dataset.count} Contributions`;
    tooltip.classList.add("is-visible");
    moveTooltip(event);
}

function moveTooltip(event) {
    if ("clientX" in event && event.clientX) {
        tooltip.style.left = `${event.clientX + 12}px`;
        tooltip.style.top = `${event.clientY + 12}px`;
        return;
    }

    const rect = event.currentTarget.getBoundingClientRect();
    tooltip.style.left = `${rect.left + rect.width + 12}px`;
    tooltip.style.top = `${rect.top}px`;
}

function hideTooltip() {
    tooltip.classList.remove("is-visible");
}

function updateDashboard(developer) {
    showLoading();

    window.requestAnimationFrame(() => {
        if (!developer) {
            selectedDeveloperLabel.textContent = "Please select a developer";

            statNodes.forEach((node) => {
                const key = node.dataset.stat;

                const emptyValues = {
                    selected_user_contributions: 0,
                    current_streak: 0,
                    longest_streak: 0,
                    most_active_day: "N/A",
                    most_active_weekday: "N/A",
                    most_active_month: "N/A",
                    average_contributions_per_day: 0,
                    calendar_summary: "Please select a developer",
                };

                node.textContent = emptyValues[key] ?? 0;
            });

            updateUserContributionTotals("");
            renderHeatmap("");
            clearDetails("");
            hideLoading();

            return;
        }

        updateStatistics(developer);
        updateUserContributionTotals(developer);
        renderHeatmap(developer);
        clearDetails(developer);
        hideLoading();
    });
}

if (developerSelect) {
    developerSelect.addEventListener("change", () => {
        updateDashboard(developerSelect.value);
    });
}

if (topContributorYear) {
    topContributorYear.addEventListener("change", () => {
        renderTopContributors(topContributorYear.value);
    });
}

renderTopContributors(
    topContributorYear
        ? topContributorYear.value
        : dashboardData.selectedTopContributorYear
);
updateDashboard("");