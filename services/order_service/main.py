import os

from fastapi import FastAPI

from .config import settings
from .database import lifespan
from .routers.orders import router as orders_router


app = FastAPI(
    title="Order Service",
    description="Microservice for cart and order processing",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(orders_router)


@app.get("/")
def root():
    return {
        "message": "Order Service is running",
        "service": settings.service_name,
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("SERVICE_PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
