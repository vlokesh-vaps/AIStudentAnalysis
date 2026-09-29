# Agent Guide

## Project overview
This project is a Flask-based AI student performance analyzer. It parses class reports from CSV, Excel, and PDF files, extracts student marks, and generates class-level and student-level academic insights using Groq LLMs. The application is designed to help teachers and administrators review student performance, identify weak and strong performers, and generate actionable recommendations.

## What this project does
- Uploads academic reports in CSV, XLS, XLSX, and PDF format.
- Extracts student names and subject scores from uploaded reports.
- Calculates totals, averages, and subject counts.
- Analyzes class performance to identify top and weak performers.
- Produces personalized student summaries and improvement strategy suggestions.
- Exposes these features via a web UI and REST APIs.

## Repository structure
- `app.py` – Flask app bootstrap and route setup.
- `config.py` – app settings and environment variables.
- `api/` – Flask-RESTX namespaces for upload and analysis endpoints.
- `services/` – file parsing, AI integration, and analysis logic.
- `templates/` – frontend HTML templates.
- `static/` – JavaScript, CSS, and frontend assets.
- `tests/` – test suite for parsing and validation logic.
- `README.md` – project usage and setup reference.
- `Dockerfile` – container setup for running the app on port 8051.

## Agent responsibilities
This agent is expected to fully inspect, modify, and improve the codebase as needed.
- Read project files to understand implementation and behavior.
- Edit existing files to fix issues, add features, or improve reliability.
- Create new files when required by the feature or refactor.
- Update project documentation and setup instructions when behavior changes.
- Run relevant tests and checks after making code changes.
- Build and validate Docker-based runs when container behavior is relevant.

## Working rules for the agent
- Keep the project structure organized.
- Respect the existing Flask architecture and JSON response formats.
- Prefer small, focused changes over broad rewrites.
- When fixing parsing logic, test real report input patterns.
- When changing AI logic, keep JSON outputs predictable and safe.
- If a bug is found, fix it directly in the relevant module instead of only describing it.
- Make sure the app can be run locally and in Docker without breaking the expected workflows.

## Environment setup
Use Python 3.11+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Add your Groq API key to `.env`:

```env
GROQ_API_KEY=your_key_here
```

## Run the app locally
```powershell
flask --app app run --port 8051
```

Open these in the browser:
- http://localhost:8051
- http://localhost:8051/swagger

## Run with Docker
```powershell
docker build -t ai-student-analysis .
docker run -p 8051:8051 --env PORT=8051 ai-student-analysis
```

Open these in the browser:
- http://localhost:8051
- http://localhost:8051/swagger

## Key APIs
- `POST /api/upload` – upload a report file and parse students.
- `POST /api/analyze/class` – analyze class performance.
- `POST /api/analyze/student` – analyze a single student.
- `GET /api/health` – health check.

## Core implementation notes
- `services/parser.py` handles CSV, XLS/XLSX, and PDF parsing.
- `services/ai.py` calls Groq and validates JSON responses.
- `api/upload.py` validates uploaded files and returns parsed student records.
- `api/class_analysis.py` and `api/student_analysis.py` implement analysis endpoints.
- Preserve the frontend and API contract when making changes.
- The project is designed so the agent can read, write, update, and validate the codebase independently.

## Validation
Run the repository tests with:

```powershell
pytest
```

## Important constraints
- AI features require a valid `GROQ_API_KEY` in `.env`.
- Uploaded files are limited to 25 MB by config.
- Parsing should be resilient to missing values, grade strings, and inconsistent report formats.
- The agent must be able to read the code, write patches, and update the project without requiring manual intervention from a human developer for routine changes.
- Docker runs should expose the application on port 8051 and keep the runtime configuration aligned with that port.
