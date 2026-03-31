"""Online Food Ordering API — Swagger at /docs."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import is_database_connected, lifespan
from app.routers import auth as auth_router
from app.routers import menu as menu_router
from app.routers import orders as orders_router

app = FastAPI(
    title="Online Food Ordering API",
    description="MVP backend — auth with MongoDB + JWT. Use **Authorize** in Swagger after `/auth/login`.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/auth", tags=["Auth"])
app.include_router(menu_router.router, prefix="/menu", tags=["Menu"])
app.include_router(orders_router.router, prefix="/orders", tags=["Orders"])


@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "database": "connected" if is_database_connected() else "disconnected",
    }
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "API Gateway is running",
    }
def root() -> dict[str, str]:
    return {
        "message": "Food Ordering API Gateway",
        "version": "0.1.0",
        "services": {
            "auth": "http://localhost:8000",
            "customers": "http://localhost:8003",
            "menu": "http://localhost:8004",
            "orders": "http://localhost:8005",
            "restaurants": "http://localhost:8006",
        },
        "docs": "/docs"
    }

