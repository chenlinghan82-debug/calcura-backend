import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.db.database import ensure_schema

ensure_schema()

app = FastAPI(
    title="Calcura API",
    version="1.1.0",
    description="A secure, backend-calculated calculator API with history, steps, and scientific operations.",
)

configured_origins = os.getenv("CALCULATOR_CORS_ORIGINS", "*")
allow_origins = [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
if not allow_origins:
    allow_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type"],
)
app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "Calcura API", "docs": "/docs", "health": "/api/health"}
