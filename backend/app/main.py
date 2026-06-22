from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.api.v1 import auth, workspaces, onboarding, sources, generate, content, schedules, credits, webhooks

settings = get_settings()

app = FastAPI(
    title="Newsletter Agent API",
    version="0.1.0",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if hasattr(exc, "status_code"):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


PREFIX = "/api/v1"

app.include_router(auth.router, prefix=PREFIX)
app.include_router(workspaces.router, prefix=PREFIX)
app.include_router(onboarding.router, prefix=PREFIX)
app.include_router(sources.router, prefix=PREFIX)
app.include_router(generate.router, prefix=PREFIX)
app.include_router(content.router, prefix=PREFIX)
app.include_router(schedules.router, prefix=PREFIX)
app.include_router(credits.router, prefix=PREFIX)
app.include_router(webhooks.router, prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
