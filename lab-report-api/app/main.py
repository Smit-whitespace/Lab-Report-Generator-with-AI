from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.db.database import engine
from app.db.base import Base
from app.db.migrations import run_startup_migrations
from app.core.config import ALLOWED_IPS
from app.api.routes import auth, user, test_template, audit_log, export, hospital, setting
from app.api.routes import test_record

app = FastAPI(title="Lab Report Generator API")
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

Base.metadata.create_all(bind=engine)
run_startup_migrations(engine)


@app.middleware("http")
async def restrict_by_ip(request: Request, call_next):
    client_ip = request.client.host if request.client else None
    if ALLOWED_IPS and client_ip not in ALLOWED_IPS:
        return JSONResponse(
            status_code=403,
            content={"detail": "Access from this IP address is not allowed"},
        )

    response = await call_next(request)
    if request.url.path == "/app" or request.url.path.startswith("/frontend"):
        response.headers["Cache-Control"] = "no-store"

    return response


app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(user.router, prefix="/users", tags=["Users"])
app.include_router(test_template.router, prefix="/templates", tags=["Templates"])   
app.include_router(test_record.router, prefix="/records", tags=["Records"])
app.include_router(audit_log.router, prefix="/audit-logs", tags=["Audit Logs"])
app.include_router(export.router, prefix="/exports", tags=["Exports"])
app.include_router(hospital.router, prefix="/hospital", tags=["Hospital"])
app.include_router(setting.router, prefix="/settings", tags=["Settings"])
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")


@app.get("/app", include_in_schema=False)
def frontend_app():
    return FileResponse(FRONTEND_DIR / "index.html")

@app.get("/")
def root():
    return {"message": "API is running"}
