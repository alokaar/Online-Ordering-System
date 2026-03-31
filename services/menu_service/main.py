import os

from fastapi import FastAPI

from .config import settings
from .database import lifespan
from .routers.menu import router as menu_router


app = FastAPI(
    title="Menu Service",
    description="Microservice for managing menu items",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(menu_router)


@app.get("/")
def root():
    return {
        "message": "Menu Service is running",
        "service": settings.service_name,
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("SERVICE_PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
