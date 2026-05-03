# Lab Report API

Production-ready FastAPI service and lightweight frontend for generating, storing, and retrieving lab reports.

Contents
- app/ — FastAPI backend (routes, models, DB).
- frontend/ — static UI (index.html, app.js, styles.css).
- requirements.txt — Python dependencies.
- .env — environment overrides.

Built with
- FastAPI, Pydantic
- SQLAlchemy (or equivalent persistence layer)
- Report generation tools (e.g., ReportLab)
- Optional integrations: OpenAI client (present in environment), other analytics

Quickstart (local)
1. Clone
    git clone https://github.com/Smit-whitespace/Lab-Report-Generator-with-AI && cd lab-report-api

2. Create venv and install
    python -m venv .venv
    .venv\Scripts\activate  (Windows) or source .venv/bin/activate (macOS/Linux)
    pip install -r requirements.txt

3. Configure environment
    Create `.env` and set required keys:
    - DATABASE_URL=sqlite:///./data.db
    - STORAGE_PATH=./storage
    - SECRET_KEY=<strong-secret>
    - OPENAI_API_KEY=<optional>
    - PORT=8000

4. Initialize DB
    - If migrations exist: run the migration tool used by the project (e.g., alembic upgrade head)
    - Otherwise ensure the configured database is reachable; the app will create tables on first run if configured to do so.

5. Run backend
    uvicorn app.main:app --reload --host 0.0.0.0 --port ${PORT:-8000}

6. Open frontend
    - Quick: open frontend/index.html in a browser
    - Or serve static files from FastAPI (if configured) at http://localhost:${PORT}

API (examples)
- Health
  GET /health

- Reports
  POST /api/reports
     - Body: JSON with report payload (patient, tests, metadata)
     - Returns: report id and status (queued/generated)

  GET /api/reports/{id}
     - Returns: report metadata and download URL (PDF)

- Attachments / Storage
  GET /api/storage/{filename}

Use curl:
curl -X POST http://localhost:8000/api/reports -H "Content-Type: application/json" -d '{"patient": {...}}'

Development
- Code layout:
  - app/main.py — application entry
  - app/api/ — route definitions
  - app/models/, app/schemas/ — DB models and Pydantic schemas
  - app/db/ — DB session and migrations
- Run with auto-reload for development: uvicorn app.main:app --reload
- Linting & formatting: use black/ruff/flake8 as preferred

Testing
- Add tests under tests/ and run:
  pytest -q

Deployment
- Containerize with a small Dockerfile; expose PORT and mount persistent STORAGE_PATH.
- Use production ASGI server (uvicorn/gunicorn with uvicorn workers) behind a reverse proxy.
- Ensure secure SECRET_KEY and DB credentials in environment; enable HTTPS.

Observability
- Add structured logging and error tracking (Sentry, etc.) as needed.
- Expose metrics endpoint or integrate with Prometheus if required.

Contributing
- Fork -> branch -> PR
- Include tests for new features/bug fixes
- Follow repository coding standards

License
- MIT (or replace with project license of choice)

Contact / Support
- File issues or PRs in this repository.

Note: adapt the environment keys and DB migration steps to match project-specific tooling present in app/db and requirements.txt.