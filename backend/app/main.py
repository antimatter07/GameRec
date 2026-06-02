from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.core.rate_limiter import limiter
from app.routers import auth, users, games, library, recommendations, feedback, admin, play_queue, journal
from app.services import auth_service

app = FastAPI(
    title="Video Game Recommender API",
    description="Backend API for the Video Game Recommender System",
    version="0.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# TODO: Tighten CORS origins for production (read from settings.ALLOWED_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


@app.middleware("http")
async def csrf_guard(request: Request, call_next):
    if not request.url.path.startswith("/api"):
        return await call_next(request)

    csrf_cookie = request.cookies.get(auth_service.CSRF_COOKIE_NAME)

    if request.method not in _SAFE_METHODS:
        csrf_header = request.headers.get("X-CSRF-Token")
        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            return JSONResponse(status_code=403, content={"detail": "CSRF validation failed"})

    response = await call_next(request)

    if request.method in _SAFE_METHODS and not csrf_cookie:
        auth_service.set_csrf_cookie(response, auth_service.generate_csrf_token())

    return response

# --- Routers ---
app.include_router(auth.router,            prefix="/api/auth",            tags=["auth"])
app.include_router(users.router,           prefix="/api/users",           tags=["users"])
app.include_router(games.router,           prefix="/api/games",           tags=["games"])
app.include_router(play_queue.router,      prefix="/api/library/queue",   tags=["play-queue"])
app.include_router(library.router,         prefix="/api/library",         tags=["library"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(feedback.router,        prefix="/api/feedback",        tags=["feedback"])
app.include_router(admin.router,           prefix="/api/admin",           tags=["admin"])
app.include_router(journal.router,         prefix="/api/journal",         tags=["journal"])


@app.get("/api/health", tags=["health"])
def health_check():
    # TODO: Add liveness checks for DB and Redis connectivity
    return {"status": "ok"}
