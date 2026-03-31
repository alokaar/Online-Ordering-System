"""Online Food Ordering API Gateway — Routes to microservices
- Auth Service (port 8000): /auth/*
- Customer Service (port 8003): /customers/*
- Menu Service: /menu/*
- Order Service: /orders/*
- Restaurant Service: /restaurants/*
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Food Ordering API Gateway",
    description="API Gateway routing to microservices: Auth, Customer, Menu, Order, Restaurant",
    version="0.1.0",
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.database import is_database_connected as app_db_connected
from app.database import lifespan as app_lifespan
from services.menu_service.database import is_database_connected as menu_db_connected
from services.menu_service.database import lifespan as menu_lifespan
from services.menu_service.menu import router as menu_router


@asynccontextmanager
async def combined_lifespan(fastapi_app: FastAPI):
    # Initialize all database connections across the orchestrated services
    async with app_lifespan(fastapi_app):
        async with menu_lifespan(fastapi_app):
            yield


app = FastAPI(
    title="Online Food Ordering API - Menu Gateway",
    description="MVP backend for Menu Service.",
    version="0.1.0",
    lifespan=combined_lifespan,
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
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "message": "API Gateway is running",
    }


@app.get("/", tags=["System"])
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

        "app_database": "connected" if app_db_connected() else "disconnected",
        "menu_database": "connected" if menu_db_connected() else "disconnected",
    }


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")
