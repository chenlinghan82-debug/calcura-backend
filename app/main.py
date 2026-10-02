import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router


class TextPlainAsJsonMiddleware:
    """Let browsers send JSON as text/plain so the request stays CORS-simple."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and scope.get("method") == "POST":
            headers = []
            changed = False
            for key, value in scope.get("headers", []):
                if key.lower() == b"content-type" and b"text/plain" in value.lower():
                    headers.append((b"content-type", b"application/json"))
                    changed = True
                else:
                    headers.append((key, value))
            if changed:
                scope = dict(scope)
                scope["headers"] = headers
        await self.app(scope, receive, send)


app = FastAPI(
    title="Calcura API",
    version="1.2.0",
    description="A secure, backend-calculated calculator API with instant preview, history, steps, and scientific operations.",
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
app.add_middleware(TextPlainAsJsonMiddleware)
app.include_router(router)


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "Calcura API", "docs": "/docs", "health": "/api/health"}
