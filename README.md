# AI Student Performance Analyzer

A single-page Flask app for parsing class reports and generating AI-assisted class and student insights with Groq.

## Project overview

This project helps teachers or administrators upload student performance reports and quickly understand:

- class-wide trends and weak performers
- top-performing students
- individual student strengths and improvement areas
- actionable recommendations generated with AI

The application accepts CSV, XLSX, XLS, and PDF reports, parses subject marks, and exposes both a browser UI and JSON APIs for analysis.

## Setup

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Add your Groq API key to `.env` as `GROQ_API_KEY=...`, then start the app:

```powershell
flask --app app run
```

Open [http://localhost:5000](http://localhost:5000) for the analyzer and [http://localhost:5000/swagger](http://localhost:5000/swagger) for interactive API documentation. The UI accepts CSV, XLSX, XLS, and PDF reports. Class and student narrative analysis requires a configured Groq API key.

## Docker setup

A Dockerfile is included for containerized runs. The container exposes port 5020:

```powershell
docker build -t ai-student-analysis .
docker run -p 5020:5020 --env PORT=5020 ai-student-analysis
```

Then open:
- http://localhost:5020
- http://localhost:5020/swagger

## API

- `POST /api/upload` — multipart form field `file`
- `POST /api/analyze/class` — JSON body containing `students`
- `POST /api/analyze/student` — JSON body containing `student`
- `GET /api/health` — health status

## Development notes

- The app is built with Flask and Flask-RESTX.
- Parsing logic lives in `services/parser.py`.
- AI analysis logic lives in `services/ai.py`.
- API routes are defined in `api/`.
- The project is designed so an agent can read the codebase, make edits, and update implementation details without manual intervention for routine work.

## Parser tests

Run the included parser tests with `pytest`.
