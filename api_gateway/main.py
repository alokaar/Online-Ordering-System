"""
API Gateway — Unified Entry Point for All Microservices
Aggregates and displays all service endpoints in a single Swagger UI
Runs on Port 8001
"""

import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional, Any, Dict
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
from fastapi.openapi.utils import get_openapi

# =====================================================
# JWT SETTINGS
# =====================================================
import os
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv("../../.env")

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-change-me-use-env-JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", scopes={})

# =====================================================
# LOGGING SETUP
# =====================================================
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("api_gateway")

# =====================================================
# MODELS
# =====================================================
class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# =====================================================
# LOGGING MIDDLEWARE
# =====================================================
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(f"→ {request.method} {request.url.path}")
        try:
            response = await call_next(request)
            logger.info(f"← {response.status_code}")
            return response
        except Exception as exc:
            logger.error(f"✗ Error: {exc}")
            raise

# =====================================================
# SERVICE CONFIGURATION
# =====================================================
SERVICES = {
    "auth": {
        "name": "Authentication Service",
        "url": "http://127.0.0.1:8000",
        "port": 8000,
        "prefix": "/auth",
        "description": "User authentication, registration, and token management",
    },
    "customers": {
        "name": "Customer Service",
        "url": "http://127.0.0.1:8003",
        "port": 8003,
        "prefix": "/customers",
        "description": "Customer profile management with role-based access",
    },
    "restaurants": {
        "name": "Restaurant Service",
        "url": "http://127.0.0.1:8005",
        "port": 8005,
        "prefix": "/restaurants",
        "description": "Restaurant and menu management",
    },
    "menu": {
        "name": "Menu Service",
        "url": "http://127.0.0.1:8007",
        "port": 8007,
        "prefix": "/menu",
        "description": "Menu items and categories",
    },
    "orders": {
        "name": "Order Service",
        "url": "http://127.0.0.1:8008",
        "port": 8008,
        "prefix": "/orders",
        "description": "Order management and processing",
    },
    "deliveries": {
        "name": "Delivery Service",
        "url": "http://127.0.0.1:8006",
        "port": 8006,
        "prefix": "/deliveries",
        "description": "Delivery tracking and management",
    },
    "feedback": {
        "name": "Feedback Service",
        "url": "http://127.0.0.1:8004",
        "port": 8004,
        "prefix": "/feedbacks",
        "description": "Customer feedback, ratings, and reviews",
    },
}

# =====================================================
# APP INIT
# =====================================================
app = FastAPI(
    title="API Gateway — Food Ordering System",
    description="Unified entry point displaying all microservice endpoints",
    version="2.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)

# =====================================================
# JWT HELPER FUNCTIONS
# =====================================================
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})

async def validate_admin_access(request: Request) -> Dict[str, Any]:
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.split(" ", 1)[1].strip()
    user = await get_current_user(token)
    user_id = user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    customer_service = SERVICES.get("customers")
    if customer_service is None:
        raise HTTPException(status_code=503, detail="Customer service unavailable")

    internal_url = f"{customer_service['url']}/internal/customers/{user_id}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(internal_url)
    except httpx.RequestError as exc:
        logger.error(f"Customer service lookup failed: {exc}")
        raise HTTPException(status_code=503, detail="Customer service unavailable")

    if response.status_code != 200:
        raise HTTPException(status_code=403, detail="Could not verify user role")

    user_info = response.json()
    if user_info.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    return user_info

# =====================================================
# GATEWAY INFO ENDPOINTS
# =====================================================
@app.get("/", tags=["Gateway"])
async def root():
    """Gateway root endpoint with all services information"""
    return {
        "message": "API Gateway — Food Ordering System",
        "version": "2.0.0",
        "note": "All microservice endpoints are combined in /docs",
        "services": {service_key: {
            "name": service["name"],
            "prefix": service["prefix"],
            "description": service["description"],
            "port": service["port"]
        } for service_key, service in SERVICES.items()},
    }

@app.get("/health", tags=["Gateway"])
async def health():
    """Gateway health check"""
    return {
        "status": "ok",
        "service": "API Gateway",
        "timestamp": datetime.utcnow().isoformat(),
    }

@app.get("/services-status", tags=["Gateway"])
async def services_status():
    """Health status of all connected services"""
    result = {}
    for service_key, service_info in SERVICES.items():
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{service_info['url']}/health")
            online = response.status_code == 200
            health_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else None
        except Exception as e:
            online = False
            health_data = None
            
        result[service_key] = {
            "name": service_info["name"],
            "url": service_info["url"],
            "port": service_info["port"],
            "online": online,
            "status": "✓ Online" if online else "✗ Offline",
            "health": health_data,
        }
    return result

# =====================================================
# GENERIC PROXY ENDPOINT
# =====================================================
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy_request(path: str, request: Request):
    """
    Universal proxy endpoint that routes requests to appropriate microservice.
    """
    logger.info(f"Proxying request: {request.method} /{path}")
    
    # Extract service prefix from path
    path_parts = path.split("/", 1)
    service_prefix = path_parts[0]
    remaining_path = "/" + path_parts[1] if len(path_parts) > 1 else "/"
    
    # Find matching service
    target_service = None
    for service_key, service_info in SERVICES.items():
        if service_info["prefix"].lstrip("/") == service_prefix:
            target_service = service_info
            break
    
    if target_service is None:
        if service_prefix in SERVICES:
            target_service = SERVICES[service_prefix]
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Service '{service_prefix}' not found. Available services: {list(SERVICES.keys())}",
            )
    
    # Build target URL
    target_url = f"{target_service['url']}/{path}"
    if request.url.query:
        target_url = f"{target_url}?{request.url.query}"

    # Require admin role for menu service access
    if target_service["prefix"].lstrip("/") == "menu":
        await validate_admin_access(request)

    logger.info(f"Routing to: {target_url}")
    
    # Prepare headers (filter out problematic ones and strip ANY user-spoofed X-User headers)
    headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in ["host", "content-length", "x-user-id", "x-user-email", "x-user-role", "x-gateway-secret"]
    }
    
    # Inject universal Gateway Identity secret
    headers["X-Gateway-Secret"] = os.getenv("GATEWAY_SECRET", "super-secret-key-123")
    
    # Securely inject genuine X-Headers only if a valid JWT is provided
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.lower().startswith("bearer "):
        try:
            token = auth_header.split(" ", 1)[1].strip()
            user_data = await get_current_user(token)
            user_id = user_data.get("sub")
            if user_id:
                headers["X-User-ID"] = str(user_id)
                # Fetch true role natively from Customer Service DB
                customer_service = SERVICES.get("customers")
                if customer_service:
                    internal_url = f"{customer_service['url']}/internal/customers/{user_id}"
                    async with httpx.AsyncClient(timeout=3.0) as client:
                        resp = await client.get(internal_url)
                        if resp.status_code == 200:
                            cinfo = resp.json()
                            headers["X-User-Role"] = cinfo.get("role", "customer")
                            headers["X-User-Email"] = cinfo.get("email", "")
        except Exception as e:
            logger.warning(f"Header injection failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Get request body
    body = await request.body()
    
    # Forward request to service
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )
    except httpx.RequestError as exc:
        logger.error(f"Service '{target_service['name']}' unavailable: {exc}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unavailable: {target_service['name']} could not be reached",
        )
    
    # Exclude problematic response headers
    excluded_headers = {"content-encoding", "transfer-encoding", "connection"}
    response_headers = {
        name: value for name, value in response.headers.items()
        if name.lower() not in excluded_headers
    }
    
    logger.info(f"Response from {target_service['name']}: {response.status_code}")
    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=response_headers,
    )

# =====================================================
# AGGREGATE OPENAPI SCHEMA
# =====================================================
async def fetch_service_openapi(service_url: str) -> dict:
    """Fetch OpenAPI schema from a service"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{service_url}/openapi.json")
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.warning(f"Could not fetch OpenAPI schema from {service_url}: {e}")
    return None

def custom_openapi():
    """Generate custom OpenAPI schema that combines all services"""
    if app.openapi_schema:
        return app.openapi_schema
    
    # Start with base schema
    output = {
        "openapi": "3.0.2",
        "info": {
            "title": "API Gateway — Food Ordering System",
            "description": "Unified interface for all microservices with combined endpoints",
            "version": "2.0.0",
        },
        "servers": [
            {"url": "http://127.0.0.1:8001", "description": "Gateway"}
        ],
        "paths": {},
        "components": {
            "schemas": {},
            "securitySchemes": {
                "OAuth2PasswordBearer": {
                    "type": "oauth2",
                    "flows": {
                        "password": {
                            "tokenUrl": "/auth/login",
                            "scopes": {}
                        }
                    }
                }
            }
        },
        "security": [{"OAuth2PasswordBearer": []}],
        "tags": []
    }
    
    # Add gateway endpoints
    output["paths"]["/"] = {
        "get": {
            "summary": "Gateway Root",
            "tags": ["Gateway"],
            "responses": {
                "200": {"description": "Gateway information"}
            }
        }
    }
    
    output["paths"]["/health"] = {
        "get": {
            "summary": "Gateway Health Check",
            "tags": ["Gateway"],
            "responses": {
                "200": {"description": "Gateway is running"}
            }
        }
    }
    
    output["paths"]["/services-status"] = {
        "get": {
            "summary": "All Services Health Status",
            "tags": ["Gateway"],
            "responses": {
                "200": {"description": "Status of all connected services"}
            }
        }
    }
    
    # Add service endpoints with their service name tags
    for service_key, service_info in SERVICES.items():
        prefix = service_info["prefix"]
        service_name = service_info["name"]
        
        # Demo endpoints for each service
        if service_key == "auth":
            output["paths"][f"{prefix}/login"] = {
                "post": {
                    "summary": "User Login",
                    "tags": [service_name],
                    "requestBody": {
                        "content": {
                            "application/x-www-form-urlencoded": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "username": {"type": "string"},
                                        "password": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Login successful"}
                    }
                }
            }
            output["paths"][f"{prefix}/register"] = {
                "post": {
                    "summary": "User Registration",
                    "tags": [service_name],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "email": {"type": "string"},
                                        "password": {"type": "string"},
                                        "full_name": {"type": "string"},
                                        "role": {"type": "string", "description": "customer or restaurant"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {"description": "User registered"}
                    }
                }
            }
            output["paths"][f"{prefix}/me"] = {
                "get": {
                    "summary": "Get current authenticated user profile",
                    "tags": [service_name],
                    "responses": {
                        "200": {"description": "User profile details"}
                    }
                }
            }
            output["paths"][f"{prefix}/change-password"] = {
                "post": {
                    "summary": "Change password for authenticated user",
                    "tags": [service_name],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "current_password": {"type": "string"},
                                        "new_password": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Password changed successfully"}
                    }
                }
            }
        
        elif service_key == "customers":
            output["paths"][f"{prefix}"] = {
                "get": {
                    "summary": "List All Customers",
                    "tags": [service_name],
                    "responses": {"200": {"description": "List of customers"}}
                }
            }
            output["paths"][f"{prefix}/me"] = {
                "get": {
                    "summary": "Get own customer profile",
                    "tags": [service_name],
                    "responses": {"200": {"description": "Customer profile"}}
                }
            }
            output["paths"][f"{prefix}/{{user_id}}"] = {
                "get": {
                    "summary": "Get Customer by ID",
                    "tags": [service_name],
                    "parameters": [{"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "Customer details"}}
                },
                "patch": {
                    "summary": "Update Customer",
                    "tags": [service_name],
                    "parameters": [{"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "full_name": {"type": "string"},
                                        "phone": {"type": "string"},
                                        "address": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Customer updated"}}
                },
                "delete": {
                    "summary": "Delete Customer",
                    "tags": [service_name],
                    "parameters": [{"name": "user_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "Customer deleted"}}
                }
            }
        
        elif service_key == "restaurants":
            output["paths"][f"{prefix}"] = {
                "get": {
                    "summary": "List All Restaurants",
                    "tags": [service_name],
                    "responses": {"200": {"description": "List of restaurants"}}
                },
                "post": {
                    "summary": "Create New Restaurant",
                    "tags": [service_name],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "address": {"type": "string"},
                                        "phone": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Restaurant created"}}
                }
            }
            output["paths"][f"{prefix}/{{restaurant_id}}"] = {
                "get": {
                    "summary": "Get Restaurant Details",
                    "tags": [service_name],
                    "parameters": [{"name": "restaurant_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "Restaurant details"}}
                },
                "put": {
                    "summary": "Update Restaurant",
                    "tags": [service_name],
                    "parameters": [{"name": "restaurant_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
                    "responses": {"200": {"description": "Restaurant updated"}}
                },
                "delete": {
                    "summary": "Delete Restaurant",
                    "tags": [service_name],
                    "parameters": [{"name": "restaurant_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "Restaurant deleted"}}
                }
            }
            output["paths"][f"{prefix}/{{restaurant_id}}/menu"] = {
                "get": {
                    "summary": "Get Restaurant Menu",
                    "tags": [service_name],
                    "parameters": [{"name": "restaurant_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "Menu items"}}
                },
                "post": {
                    "summary": "Add Menu Item",
                    "tags": [service_name],
                    "parameters": [{"name": "restaurant_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "price": {"type": "number"},
                                        "description": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Menu item added"}}
                }
            }
        
        elif service_key == "menu":
            output["paths"][f"{prefix}"] = {
                "get": {
                    "summary": "List All Menu Items",
                    "tags": [service_name],
                    "parameters": [
                        {"name": "category", "in": "query", "schema": {"type": "string"}},
                        {"name": "available_only", "in": "query", "schema": {"type": "boolean"}}
                    ],
                    "responses": {"200": {"description": "List of menu items"}}
                },
                "post": {
                    "summary": "Create Menu Item",
                    "tags": [service_name],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "price": {"type": "number"},
                                        "category": {"type": "string"},
                                        "restaurant_id": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Menu item created"}}
                }
            }
            output["paths"][f"{prefix}/{{item_id}}"] = {
                "get": {
                    "summary": "Get Menu Item",
                    "tags": [service_name],
                    "parameters": [{"name": "item_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "Menu item details"}}
                },
                "put": {
                    "summary": "Update Menu Item",
                    "tags": [service_name],
                    "parameters": [{"name": "item_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
                    "responses": {"200": {"description": "Menu item updated"}}
                },
                "delete": {
                    "summary": "Delete Menu Item",
                    "tags": [service_name],
                    "parameters": [{"name": "item_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "Menu item deleted"}}
                }
            }
        
        elif service_key == "orders":
            output["paths"][f"{prefix}"] = {
                "get": {
                    "summary": "List All Orders",
                    "tags": [service_name],
                    "responses": {"200": {"description": "List of orders"}}
                },
                "post": {
                    "summary": "Create New Order",
                    "tags": [service_name],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "customer_id": {"type": "string"},
                                        "restaurant_id": {"type": "string"},
                                        "items": {"type": "array"},
                                        "total_price": {"type": "number"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Order created"}}
                }
            }
            output["paths"][f"{prefix}/{{order_id}}"] = {
                "get": {
                    "summary": "Get Order Details",
                    "tags": [service_name],
                    "parameters": [{"name": "order_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "Order details"}}
                },
                "put": {
                    "summary": "Update Order Status",
                    "tags": [service_name],
                    "parameters": [{"name": "order_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
                    "responses": {"200": {"description": "Order updated"}}
                },
                "delete": {
                    "summary": "Cancel Order",
                    "tags": [service_name],
                    "parameters": [{"name": "order_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "Order cancelled"}}
                }
            }
        
        elif service_key == "deliveries":
            output["paths"][f"{prefix}"] = {
                "get": {
                    "summary": "List All Deliveries",
                    "tags": [service_name],
                    "responses": {"200": {"description": "List of deliveries"}}
                },
                "post": {
                    "summary": "Create New Delivery",
                    "tags": [service_name],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "order_id": {"type": "string"},
                                        "driver_id": {"type": "string"},
                                        "address": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Delivery created"}}
                }
            }
            output["paths"][f"{prefix}/{{delivery_id}}"] = {
                "get": {
                    "summary": "Get Delivery Status",
                    "tags": [service_name],
                    "parameters": [{"name": "delivery_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "Delivery details"}}
                },
                "put": {
                    "summary": "Update Delivery Status",
                    "tags": [service_name],
                    "parameters": [{"name": "delivery_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
                    "responses": {"200": {"description": "Delivery updated"}}
                }
            }
        
        elif service_key == "feedback":
            output["paths"][f"{prefix}"] = {
                "post": {
                    "summary": "Submit Order Feedback",
                    "tags": [service_name],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "order_id": {"type": "string"},
                                        "rating": {"type": "integer"},
                                        "review_text": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Feedback submitted"}}
                }
            }
            output["paths"][f"{prefix}/restaurant/{{restaurant_id}}"] = {
                "post": {
                    "summary": "Submit Restaurant Feedback",
                    "tags": [service_name],
                    "parameters": [{"name": "restaurant_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "rating": {"type": "integer"},
                                        "review_text": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"201": {"description": "Feedback submitted"}}
                },
                "get": {
                    "summary": "Get Restaurant Feedbacks",
                    "tags": [service_name],
                    "parameters": [{"name": "restaurant_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "List of feedbacks for restaurant"}}
                }
            }
            output["paths"][f"{prefix}/{{feedback_id}}"] = {
                "get": {
                    "summary": "Get Feedback",
                    "tags": [service_name],
                    "parameters": [{"name": "feedback_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "Feedback details"}}
                },
                "put": {
                    "summary": "Update Feedback",
                    "tags": [service_name],
                    "parameters": [{"name": "feedback_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "rating": {"type": "integer"},
                                        "review_text": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {"200": {"description": "Feedback updated"}}
                },
                "delete": {
                    "summary": "Delete Feedback",
                    "tags": [service_name],
                    "parameters": [{"name": "feedback_id", "in": "path", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"description": "Feedback deleted"}}
                }
            }
    
    app.openapi_schema = output
    return app.openapi_schema

app.openapi = custom_openapi

# =====================================================
# ERROR HANDLERS
# =====================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error occurred")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)}
    )

# =====================================================
# STARTUP EVENTS
# =====================================================
@app.on_event("startup")
async def startup_event():
    """Log startup and check service availability"""
    logger.info("=" * 70)
    logger.info("API GATEWAY STARTING — UNIFIED MICROSERVICES INTERFACE")
    logger.info("=" * 70)
    logger.info(f"Total Services Connected: {len(SERVICES)}")
    for service_key, service_info in SERVICES.items():
        logger.info(f"  ✓ {service_info['name']:<30} ({service_info['prefix']:<15}) → {service_info['url']}")
    logger.info("=" * 70)
    logger.info("All service endpoints will appear in /docs (Swagger UI)")
    logger.info("=" * 70)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=True)
