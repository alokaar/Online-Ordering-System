import httpx
from fastapi import FastAPI, HTTPException, Request, Response

app = FastAPI(
    title="API Gateway",
    description="Unified entry point for all microservices",
    version="1.0.0",
)

# Service routing map
SERVICE_MAP = {
    "/auth": "http://127.0.0.1:8000",
    "/customer": "http://127.0.0.1:8003",
    "/restaurant": "http://127.0.0.1:8005",
    "/menu": "http://127.0.0.1:8007",
    "/order": "http://127.0.0.1:8008",
    "/delivery": "http://127.0.0.1:8006",
    "/feedback": "http://127.0.0.1:8004",
}


@app.get("/")
async def root():
    return {
        "message": "API Gateway — Unified entry point for Online Food Ordering System",
        "services": {
            "/auth": "Authentication Service (port 8000)",
            "/customer": "Customer Service (port 8003)",
            "/restaurant": "Restaurant Service (port 8005)",
            "/menu": "Menu Service (port 8007)",
            "/order": "Order Service (port 8008)",
            "/delivery": "Delivery Service (port 8006)",
            "/feedback": "Feedback Service (port 8004)",
        },
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "gateway": "running"}


@app.get("/services-status")
async def services_status():
    result = {}
    for prefix, url in SERVICE_MAP.items():
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get(f"{url}/health")
            result[prefix] = {
                "url": url,
                "status_code": r.status_code,
                "online": r.status_code == 200,
                "details": r.json() if r.headers.get("content-type", "").startswith("application/json") else None,
            }
        except Exception as e:
            result[prefix] = {"url": url, "online": False, "error": str(e)}
    return result


def fetch_service_schema(service_url: str) -> dict:
    """Fetch OpenAPI schema from a service."""
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{service_url}/openapi.json")
            if response.status_code == 200:
                return response.json()
    except Exception:
        pass
    return None


def custom_openapi():
    """Generate comprehensive OpenAPI schema with all microservice endpoints."""
    if app.openapi_schema:
        return app.openapi_schema

    # Start with gateway's base schema
    output = {
        "openapi": "3.0.2",
        "info": {
            "title": "API Gateway - Online Food Ordering System",
            "description": "Unified entry point for all microservices in the Online Food Ordering System",
            "version": "1.0.0",
        },
        "paths": {},
        "components": {
            "schemas": {}
        },
        "tags": [
            {"name": "Gateway", "description": "API Gateway endpoints"},
            {"name": "auth", "description": "Authentication Service"},
            {"name": "customer", "description": "Customer Service"},
            {"name": "restaurant", "description": "Restaurant Service"},
            {"name": "menu", "description": "Menu Service"},
            {"name": "order", "description": "Order Service"},
            {"name": "delivery", "description": "Delivery Service"},
            {"name": "feedback", "description": "Feedback Service"},
        ]
    }

    # Add gateway endpoints
    output["paths"]["/"] = {
        "get": {
            "summary": "Root - Service Information",
            "operationId": "root__get",
            "tags": ["Gateway"],
            "responses": {
                "200": {
                    "description": "Successful Response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string"},
                                    "services": {"type": "object"},
                                    "docs": {"type": "string"},
                                    "health": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    output["paths"]["/health"] = {
        "get": {
            "summary": "Gateway Health Check",
            "operationId": "health_get",
            "tags": ["Gateway"],
            "responses": {
                "200": {
                    "description": "Successful Response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "status": {"type": "string"},
                                    "gateway": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    output["paths"]["/services-status"] = {
        "get": {
            "summary": "Check status of all microservices",
            "operationId": "services_status_get",
            "tags": ["Gateway"],
            "responses": {
                "200": {
                    "description": "Service status information",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "additionalProperties": {
                                    "type": "object",
                                    "properties": {
                                        "url": {"type": "string"},
                                        "online": {"type": "boolean"},
                                        "status_code": {"type": "integer"},
                                        "details": {"type": "object"},
                                        "error": {"type": "string"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    # Add comprehensive endpoints for all services
    # Auth Service endpoints
    output["paths"]["/auth/login"] = {
        "post": {
            "summary": "User login",
            "operationId": "auth_login_post",
            "tags": ["auth"],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "username": {"type": "string"},
                                "password": {"type": "string"}
                            },
                            "required": ["username", "password"]
                        }
                    }
                }
            },
            "responses": {
                "200": {"description": "Login successful"},
                "401": {"description": "Invalid credentials"}
            }
        }
    }

    output["paths"]["/auth/register"] = {
        "post": {
            "summary": "User registration",
            "operationId": "auth_register_post",
            "tags": ["auth"],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "username": {"type": "string"},
                                "email": {"type": "string"},
                                "password": {"type": "string"},
                                "role": {"type": "string", "enum": ["admin", "restaurant", "customer", "guest"]}
                            },
                            "required": ["username", "email", "password"]
                        }
                    }
                }
            },
            "responses": {
                "201": {"description": "User registered successfully"},
                "400": {"description": "Invalid input"}
            }
        }
    }

    output["paths"]["/auth/me"] = {
        "get": {
            "summary": "Get current user info",
            "operationId": "auth_me_get",
            "tags": ["auth"],
            "responses": {
                "200": {"description": "User information"},
                "401": {"description": "Not authenticated"}
            }
        }
    }

    # Customer Service endpoints
    output["paths"]["/customer/me"] = {
        "get": {
            "summary": "Get my profile",
            "operationId": "customer_me_get",
            "tags": ["customer"],
            "responses": {
                "200": {"description": "Customer profile"},
                "401": {"description": "Not authenticated"}
            }
        }
    }

    output["paths"]["/customer/{customer_id}"] = {
        "get": {
            "summary": "Get customer by ID",
            "operationId": "customer_customer_id_get",
            "tags": ["customer"],
            "parameters": [
                {
                    "name": "customer_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }
            ],
            "responses": {
                "200": {"description": "Customer information"},
                "404": {"description": "Customer not found"}
            }
        },
        "patch": {
            "summary": "Update customer profile",
            "operationId": "customer_customer_id_patch",
            "tags": ["customer"],
            "parameters": [
                {
                    "name": "customer_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }
            ],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "email": {"type": "string"},
                                "phone": {"type": "string"},
                                "address": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "responses": {
                "200": {"description": "Profile updated"},
                "404": {"description": "Customer not found"}
            }
        }
    }

    # Restaurant Service endpoints
    output["paths"]["/restaurant"] = {
        "get": {
            "summary": "Get all restaurants",
            "operationId": "restaurant_get",
            "tags": ["restaurant"],
            "responses": {
                "200": {"description": "List of restaurants"}
            }
        },
        "post": {
            "summary": "Create new restaurant",
            "operationId": "restaurant_post",
            "tags": ["restaurant"],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "address": {"type": "string"},
                                "phone": {"type": "string"}
                            },
                            "required": ["name", "address"]
                        }
                    }
                }
            },
            "responses": {
                "201": {"description": "Restaurant created"},
                "400": {"description": "Invalid input"}
            }
        }
    }

    output["paths"]["/restaurant/{restaurant_id}"] = {
        "get": {
            "summary": "Get restaurant by ID",
            "operationId": "restaurant_restaurant_id_get",
            "tags": ["restaurant"],
            "parameters": [
                {
                    "name": "restaurant_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }
            ],
            "responses": {
                "200": {"description": "Restaurant information"},
                "404": {"description": "Restaurant not found"}
            }
        },
        "put": {
            "summary": "Update restaurant",
            "operationId": "restaurant_restaurant_id_put",
            "tags": ["restaurant"],
            "parameters": [
                {
                    "name": "restaurant_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }
            ],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "address": {"type": "string"},
                                "phone": {"type": "string"}
                            }
                        }
                    }
                }
            },
            "responses": {
                "200": {"description": "Restaurant updated"},
                "404": {"description": "Restaurant not found"}
            }
        },
        "delete": {
            "summary": "Delete restaurant",
            "operationId": "restaurant_restaurant_id_delete",
            "tags": ["restaurant"],
            "parameters": [
                {
                    "name": "restaurant_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }
            ],
            "responses": {
                "200": {"description": "Restaurant deleted"},
                "404": {"description": "Restaurant not found"}
            }
        }
    }

    output["paths"]["/restaurant/{restaurant_id}/menu"] = {
        "get": {
            "summary": "Get restaurant menu",
            "operationId": "restaurant_restaurant_id_menu_get",
            "tags": ["restaurant"],
            "parameters": [
                {
                    "name": "restaurant_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }
            ],
            "responses": {
                "200": {"description": "Restaurant menu"},
                "404": {"description": "Restaurant not found"}
            }
        },
        "post": {
            "summary": "Add menu item",
            "operationId": "restaurant_restaurant_id_menu_post",
            "tags": ["restaurant"],
            "parameters": [
                {
                    "name": "restaurant_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }
            ],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "price": {"type": "number"},
                                "category": {"type": "string"},
                                "is_available": {"type": "boolean"}
                            },
                            "required": ["name", "price"]
                        }
                    }
                }
            },
            "responses": {
                "201": {"description": "Menu item added"},
                "404": {"description": "Restaurant not found"}
            }
        }
    }

    # Menu Service endpoints
    output["paths"]["/menu"] = {
        "get": {
            "summary": "Get all menu items",
            "operationId": "menu_get",
            "tags": ["menu"],
            "parameters": [
                {
                    "name": "category",
                    "in": "query",
                    "schema": {"type": "string"}
                },
                {
                    "name": "available_only",
                    "in": "query",
                    "schema": {"type": "boolean"}
                }
            ],
            "responses": {
                "200": {"description": "List of menu items"}
            }
        },
        "post": {
            "summary": "Create menu item",
            "operationId": "menu_post",
            "tags": ["menu"],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "price": {"type": "number"},
                                "category": {"type": "string"},
                                "restaurant_id": {"type": "string"},
                                "is_available": {"type": "boolean"}
                            },
                            "required": ["name", "price", "restaurant_id"]
                        }
                    }
                }
            },
            "responses": {
                "201": {"description": "Menu item created"},
                "400": {"description": "Invalid input"}
            }
        }
    }

    output["paths"]["/menu/{item_id}"] = {
        "get": {
            "summary": "Get menu item by ID",
            "operationId": "menu_item_id_get",
            "tags": ["menu"],
            "parameters": [
                {
                    "name": "item_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }
            ],
            "responses": {
                "200": {"description": "Menu item details"},
                "404": {"description": "Menu item not found"}
            }
        },
        "put": {
            "summary": "Update menu item",
            "operationId": "menu_item_id_put",
            "tags": ["menu"],
            "parameters": [
                {
                    "name": "item_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }
            ],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "price": {"type": "number"},
                                "category": {"type": "string"},
                                "is_available": {"type": "boolean"}
                            }
                        }
                    }
                }
            },
            "responses": {
                "200": {"description": "Menu item updated"},
                "404": {"description": "Menu item not found"}
            }
        },
        "delete": {
            "summary": "Delete menu item",
            "operationId": "menu_item_id_delete",
            "tags": ["menu"],
            "parameters": [
                {
                    "name": "item_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }
            ],
            "responses": {
                "200": {"description": "Menu item deleted"},
                "404": {"description": "Menu item not found"}
            }
        }
    }

    # Order Service endpoints
    output["paths"]["/order/cart"] = {
        "get": {
            "summary": "Get current cart",
            "operationId": "order_cart_get",
            "tags": ["order"],
            "responses": {
                "200": {"description": "Current cart items"}
            }
        }
    }

    output["paths"]["/order/cart/add"] = {
        "post": {
            "summary": "Add item to cart",
            "operationId": "order_cart_add_post",
            "tags": ["order"],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "menu_item_id": {"type": "string"},
                                "quantity": {"type": "integer", "minimum": 1}
                            },
                            "required": ["menu_item_id", "quantity"]
                        }
                    }
                }
            },
            "responses": {
                "200": {"description": "Item added to cart"},
                "404": {"description": "Menu item not found"}
            }
        }
    }

    output["paths"]["/order/cart/checkout"] = {
        "post": {
            "summary": "Checkout cart",
            "operationId": "order_cart_checkout_post",
            "tags": ["order"],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "delivery_address": {"type": "string"},
                                "payment_method": {"type": "string"}
                            },
                            "required": ["delivery_address"]
                        }
                    }
                }
            },
            "responses": {
                "201": {"description": "Order created"},
                "400": {"description": "Invalid cart or input"}
            }
        }
    }

    output["paths"]["/order"] = {
        "get": {
            "summary": "Get user orders",
            "operationId": "order_get",
            "tags": ["order"],
            "responses": {
                "200": {"description": "List of user orders"}
            }
        }
    }

    output["paths"]["/order/{order_id}"] = {
        "get": {
            "summary": "Get order by ID",
            "operationId": "order_order_id_get",
            "tags": ["order"],
            "parameters": [
                {
                    "name": "order_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }
            ],
            "responses": {
                "200": {"description": "Order details"},
                "404": {"description": "Order not found"}
            }
        }
    }

    # Delivery Service endpoints
    output["paths"]["/delivery/orders/{order_id}"] = {
        "get": {
            "summary": "Get delivery status for order",
            "operationId": "delivery_orders_order_id_get",
            "tags": ["delivery"],
            "parameters": [
                {
                    "name": "order_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }
            ],
            "responses": {
                "200": {"description": "Delivery status"},
                "404": {"description": "Order not found"}
            }
        },
        "post": {
            "summary": "Assign delivery for order",
            "operationId": "delivery_orders_order_id_post",
            "tags": ["delivery"],
            "parameters": [
                {
                    "name": "order_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }
            ],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "delivery_person_id": {"type": "string"},
                                "estimated_delivery_time": {"type": "string"}
                            },
                            "required": ["delivery_person_id"]
                        }
                    }
                }
            },
            "responses": {
                "200": {"description": "Delivery assigned"},
                "404": {"description": "Order not found"}
            }
        }
    }

    # Feedback Service endpoints
    output["paths"]["/feedback"] = {
        "post": {
            "summary": "Submit feedback",
            "operationId": "feedback_post",
            "tags": ["feedback"],
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "order_id": {"type": "string"},
                                "rating": {"type": "integer", "minimum": 1, "maximum": 5},
                                "comment": {"type": "string"},
                                "customer_id": {"type": "string"}
                            },
                            "required": ["order_id", "rating"]
                        }
                    }
                }
            },
            "responses": {
                "201": {"description": "Feedback submitted"},
                "400": {"description": "Invalid input"}
            }
        }
    }

    output["paths"]["/feedback/order/{order_id}"] = {
        "get": {
            "summary": "Get feedback for order",
            "operationId": "feedback_order_order_id_get",
            "tags": ["feedback"],
            "parameters": [
                {
                    "name": "order_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }
            ],
            "responses": {
                "200": {"description": "Order feedback"},
                "404": {"description": "Feedback not found"}
            }
        }
    }

    output["paths"]["/feedback/restaurant/{restaurant_id}"] = {
        "get": {
            "summary": "Get feedback for restaurant",
            "operationId": "feedback_restaurant_restaurant_id_get",
            "tags": ["feedback"],
            "parameters": [
                {
                    "name": "restaurant_id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }
            ],
            "responses": {
                "200": {"description": "Restaurant feedback"}
            }
        }
    }

    app.openapi_schema = output
    return app.openapi_schema


app.openapi = custom_openapi


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
async def proxy(path: str, request: Request):
    """
    Proxy all requests to appropriate microservice based on path prefix.
    No authentication, authorization, or modification — pure passthrough.
    """
    # Extract service prefix
    prefix = "/" + path.split("/")[0] if path else "/"
    target_base = SERVICE_MAP.get(prefix)

    if target_base is None:
        raise HTTPException(
            status_code=404,
            detail=f"Service not found for prefix: {prefix}. Available: {list(SERVICE_MAP.keys())}",
        )

    # Build target URL
    url = target_base.rstrip("/") + "/" + path
    if request.url.query:
        url = f"{url}?{request.url.query}"

    # Forward headers (exclude problematic ones)
    headers = {
        k: v
        for k, v in request.headers.items()
        if k.lower() not in ["host", "content-length"]
    }

    # Get request body
    body = await request.body()

    # Forward request to service
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Service unavailable: {str(exc)}",
            )

    # Forward response (exclude problematic headers)
    excluded_headers = {"content-encoding", "transfer-encoding", "connection"}
    response_headers = {
        name: value
        for name, value in response.headers.items()
        if name.lower() not in excluded_headers
    }

    return Response(
        content=response.content,
        status_code=response.status_code,
        headers=response_headers,
    )
