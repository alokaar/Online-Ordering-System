import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .config import settings
from .database import lifespan, is_database_connected
from .menu import router as menu_router

app = FastAPI(
    title="Online Food Ordering API - Menu Service",
    description="Microservice for managing menu items",
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

app.include_router(menu_router, prefix="/menu", tags=["Menu"])


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.service_name,
        "database": "connected" if is_database_connected() else "disconnected",
    }


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("SERVICE_PORT", 8007))
    uvicorn.run(app, host="0.0.0.0", port=port)
