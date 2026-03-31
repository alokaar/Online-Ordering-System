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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

