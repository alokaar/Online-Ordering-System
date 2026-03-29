"""Online Food Ordering API — Swagger at /docs."""

from fastapi import FastAPI

from app.database import is_database_connected, lifespan
from app.routers import auth as auth_router

app = FastAPI(
    title="Online Food Ordering API",
    description="MVP backend — auth with MongoDB + JWT. Use **Authorize** in Swagger after `/auth/login`.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth_router.router, prefix="/auth", tags=["Auth"])


@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "database": "connected" if is_database_connected() else "disconnected",
    }


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    return {"message": "Online Food Ordering — use /docs for Swagger UI"}
