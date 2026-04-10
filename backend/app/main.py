from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.routers import auth, users, games, library, recommendations, feedback, admin, play_queue

# TODO: Replace with the user-aware key function from app.core.rate_limiter
limiter = Limiter(key_func=get_remote_address)

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

# --- Routers ---
app.include_router(auth.router,            prefix="/api/auth",            tags=["auth"])
app.include_router(users.router,           prefix="/api/users",           tags=["users"])
app.include_router(games.router,           prefix="/api/games",           tags=["games"])
app.include_router(library.router,         prefix="/api/library",         tags=["library"])
app.include_router(play_queue.router,      prefix="/api/library/queue",   tags=["play-queue"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(feedback.router,        prefix="/api/feedback",        tags=["feedback"])
app.include_router(admin.router,           prefix="/api/admin",           tags=["admin"])


@app.get("/api/health", tags=["health"])
def health_check():
    # TODO: Add liveness checks for DB and Redis connectivity
    return {"status": "ok"}
