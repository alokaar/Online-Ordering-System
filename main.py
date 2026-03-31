"""Online Food Ordering API — Swagger at /docs."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import is_database_connected, lifespan
from app.routers import menu as menu_router
from app.routers import orders as orders_router

app = FastAPI(
    title="Online Food Ordering API",
    description="MVP backend.",
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

app.include_router(menu_router.router, prefix="/menu", tags=["Menu"])
app.include_router(orders_router.router, prefix="/orders", tags=["Orders"])


@app.get("/health", tags=["System"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "database": "connected" if is_database_connected() else "disconnected",
    }


@app.get("/", include_in_schema=False)
def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")

