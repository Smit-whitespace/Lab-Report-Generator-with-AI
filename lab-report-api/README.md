# Lab Report Generator with AI

A full-stack lab report management system built with FastAPI. Handles the complete workflow — from report creation and PDF generation to role-based access and AI-assisted clinical summaries — with all core features running fully offline.

![Dashboard Screenshot](./screenshots/dashboard.png)

---

## What It Does

Lab staff log in and create reports by entering patient details and test results. The system stores everything, generates a formatted PDF, and — when an OpenAI API key is configured — adds an AI-generated clinical summary to the report.

**Example AI summary:**
> Hemoglobin and RBC values are below typical reference ranges. Clinical correlation is recommended. Please review alongside patient history and other investigations.

If no API key is present or the request fails, the system falls back gracefully and the rest of the report is unaffected.

---

## Role-Based Access Control

| Role | Permissions |
|---|---|
| **Admin** | Manage users, test templates, hospital settings, AI settings, exports, audit logs |
| **Technician** | Create reports, enter lab results, generate and download PDFs, view records |
| **Doctor** | View reports, view AI summaries, download PDFs (read-only) |

---

## Offline-First Architecture

All core functionality runs on your local machine or server with no internet required:

- Login and authentication
- User management
- Test template management
- Lab report creation and storage
- PDF generation
- Audit logs
- Hospital settings
- Record viewing and search

The only feature requiring internet is AI summary generation. If unavailable, the app returns a clear error and continues normally.

---

## Tech Stack

- **Backend** — FastAPI, Python
- **Database** — SQLite (V1) · PostgreSQL (V2, current)
- **PDF Generation** — ReportLab
- **AI Integration** — OpenAI API (optional)
- **Frontend** — Vanilla HTML/CSS/JS

---

## Quickstart

**1. Clone the repo**
```bash
git clone https://github.com/Smit-whitespace/Lab-Report-Generator-with-AI
cd Lab-Report-Generator-with-AI
```

**2. Create a virtual environment and install dependencies**
```bash
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

**3. Configure environment**

Create a `.env` file in the root directory:
```env
DATABASE_URL=sqlite:///./data.db
STORAGE_PATH=./storage
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=sk-...            # Optional — AI summaries only
PORT=8000
```

**4. Run the backend**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**5. Open the frontend**

Open `frontend/index.html` in a browser, or navigate to `http://localhost:8000` if static files are served by FastAPI.

---

## API Overview

```
GET  /health                    # Health check
POST /api/reports               # Create a new report
GET  /api/reports/{id}          # Fetch report metadata and PDF URL
GET  /api/storage/{filename}    # Download stored file
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/reports \
  -H "Content-Type: application/json" \
  -d '{"patient": {"name": "John Doe", "age": 34}, "tests": [...]}'
```

---

## Project Structure

```
app/
├── main.py          # Application entry point
├── api/             # Route definitions
├── models/          # Database models
├── schemas/         # Pydantic schemas
└── db/              # Database session and setup
frontend/
├── index.html
├── app.js
└── styles.css
```

---

## License

MIT
