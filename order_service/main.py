import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from .config import settings
from .database import lifespan as order_lifespan
from .orders import router as orders_router
from app.database import lifespan as app_lifespan

@asynccontextmanager
async def combined_lifespan(fastapi_app: FastAPI):
    # Enable db connections strictly orchestrating the Order service
    async with app_lifespan(fastapi_app):
        async with order_lifespan(fastapi_app):
            yield


app = FastAPI(
    title="Online Order Service",
    description="Microservice for cart, menu fetching, and order processing",
    version="0.1.0",
    lifespan=combined_lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders_router, prefix="", tags=["Orders"])


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.service_name,
    }


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("SERVICE_PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
