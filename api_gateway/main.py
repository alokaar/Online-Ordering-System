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
            "/auth": "Authentication Service (port 8002)",
            "/customer": "Customer Service (port 8003)",
            "/restaurant": "Restaurant Service (port 8005)",
            "/menu": "Menu Service (port 8007)",
            "/order": "Order Service (port 8008)",
            "/delivery": "Delivery Service (port 8009)",
            "/feedback": "Feedback Service (port 8010)",
        },
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "gateway": "running"}


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
