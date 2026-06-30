from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import init_db
from app.routers.reports import router as reports_router


app = FastAPI(
    title=settings.project_name,
    description="Rule-based Clash Royale roast dashboard with no paid LLM dependency.",
    version="1.0.0",
)

allowed_origins = {
    settings.frontend_origin,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/")
def root() -> dict[str, str]:
    return {"name": settings.project_name, "status": "ready"}


@app.get("/api/health")
def health() -> dict[str, object]:
    return {"status": "ok", "mock_mode": settings.use_mock_data}


app.include_router(reports_router, prefix="/api")

