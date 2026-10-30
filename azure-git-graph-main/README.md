# Azure DevOps Insights

Azure DevOps Insights is a Python Flask application that reads Azure DevOps TFVC changesets and displays developer contribution activity in a GitHub-style calendar.

The application uses only:

- Python 3.11+
- Flask
- requests
- HTML, CSS, and vanilla JavaScript

No React, database, ORM, Bootstrap, chart library, or canvas is required.

## Features

- Azure DevOps TFVC REST API integration
- Service layer for API access
- Separate analytics/business logic layer
- In-memory processed dashboard cache
- Developer dropdown with no page reload
- GitHub-style 365-day contribution heatmap
- CSS Grid calendar with weeks as columns and days as rows
- Contribution tooltip on hover/focus
- Clickable heatmap squares with changeset details
- Details panel showing changeset ID, comment, and time
- Current streak and longest streak
- Most active day, weekday, and month
- Average contributions per active day
- Contribution calendar summary
- Sticky header, loading spinner, empty state, and responsive layout
- Friendly error message when the Azure DevOps API is down

## Project Structure

```text
azure-devops-insights/
    app.py
    requirements.txt
    README.md
    .gitignore
    services/
        analytics.py
        tfvc.py
    static/
        app.js
        style.css
    templates/
        base.html
        index.html
```

## Install On A New PC

1. Install Python 3.11 or newer.

Check Python:

```powershell
python --version
```

2. Clone the repository.

```powershell
git clone <your-github-repository-url>
cd azure-devops-insights
```

3. Create a virtual environment.

```powershell
python -m venv .venv
```

4. Activate the virtual environment.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

macOS/Linux:

```bash
source .venv/bin/activate
```

5. Install dependencies.

```powershell
pip install -r requirements.txt
```

6. Run the application.

```powershell
python app.py
```

7. Open the dashboard.

```text
http://127.0.0.1:5000
```

## Azure DevOps API

The app currently calls:

```text
http://10.64.33.98:8080/tfs/SLAM_APPLICATION/SLAM_PROD/_apis/tfvc/changesets?$top=10000&api-version=5.0
```

The API URL is defined in:

```text
services/tfvc.py
```

If the API is down or unreachable, the Flask page still loads and shows a friendly error panel instead of crashing.

## Development Notes

- Keep all Azure DevOps API logic in `services/tfvc.py`.
- Keep dashboard processing and statistics in `services/analytics.py`.
- Keep UI behavior in `static/app.js`.
- Keep styling in `static/style.css`.
- Do not commit `.venv`, `__pycache__`, logs, or local environment files.

## GitHub Push Checklist

Before pushing:

```powershell
git status
```

Make sure these are not staged:

```text
.venv/
__pycache__/
*.log
.env
```

Then commit:

```powershell
git add .
git commit -m "Build Azure DevOps Insights dashboard"
git push
```

## Future Improvements

- Add a manual refresh button for the in-memory cache
- Move the TFVC API URL to environment configuration
- Add optional Azure DevOps authentication headers
- Add date-range filtering
- Add project or branch filters
- Export selected developer contributions to CSV
- Add unit tests for analytics functions
- Add production WSGI deployment instructions
