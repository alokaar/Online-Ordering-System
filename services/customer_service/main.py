"""Customer Service Microservice — Main Entry Point
Handles User Profile Management with Role-Based Access Control
Runs on Port 8003 (direct) and accessible via API Gateway Port 8000
"""

import logging
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from .config import settings
from .database import get_database, is_database_connected, lifespan
from .models import (
    CustomerCreate,
    CustomerListOut,
    CustomerOut,
    CustomerUpdate,
    HealthResponse,
    UserRole,
)
from .service import (
    CustomerService,
    RBACContext,
    RBACService,
    get_customer_service,
    get_rbac_context,
    require_role,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app with lifespan
app = FastAPI(
    title="Customer Service",
    description="Microservice for managing customer profiles with Role-Based Access Control (RBAC)",
    version="0.1.0",
    lifespan=lifespan,
)


# ============================================================================
# HEALTH & SYSTEM ENDPOINTS
# ============================================================================


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check() -> HealthResponse:
    """Health check endpoint — shows service and database status"""
    return HealthResponse(
        service="Customer Service",
        status="running",
        database="connected" if is_database_connected() else "disconnected",
    )


@app.get("/", tags=["System"])
async def root() -> dict[str, str]:
    """Root endpoint with service information"""
    return {
        "service": "Customer Service",
        "version": "0.1.0",
        "port": settings.service_port,
        "docs": "/docs",
    }


# ============================================================================
# CUSTOMER ENDPOINTS — WITH RBAC
# ============================================================================


@app.post(
    "/customers",
    response_model=CustomerOut,
    status_code=status.HTTP_201_CREATED,
    tags=["Customers"],
)
async def create_customer_profile(
    customer_data: CustomerCreate,
    rbac_context: Annotated[RBACContext, Depends(get_rbac_context)],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerOut:
    """
    Create a new customer profile.
    - ADMIN, CUSTOMER, RESTAURANT: Can create profiles
    - The user_id in the request should match the authenticated user (except ADMIN)
    - Role is automatically set from JWT token (via Gateway header)
    """
    rbac = RBACService(rbac_context.role)

    # ADMIN can create for anyone, others must create for themselves
    if rbac_context.role != UserRole.ADMIN and customer_data.user_id != rbac_context.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create customer profile for another user",
        )

    # Override role with the one from JWT token (passed via header from Gateway)
    customer_data.role = rbac_context.role

    logger.info(
        f"Creating customer profile | user_id={customer_data.user_id} | role={rbac_context.role}"
    )
    return await service.create_customer(customer_data)


@app.get(
    "/customers/me",
    response_model=CustomerOut,
    tags=["Customers"],
)
async def get_own_customer_profile(
    rbac_context: Annotated[RBACContext, Depends(get_rbac_context)],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerOut:
    """Get current user's customer profile"""
    customer = await service.get_customer_by_user_id(rbac_context.user_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found",
        )

    logger.info(f"Retrieved own customer profile | user_id={rbac_context.user_id}")
    return customer


@app.get(
    "/customers/{customer_id}",
    response_model=CustomerOut,
    tags=["Customers"],
)
async def get_customer_by_id(
    customer_id: str,
    rbac_context: Annotated[RBACContext, Depends(get_rbac_context)],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerOut:
    """
    Get customer by ID.
    - ADMIN: Can view any customer
    - CUSTOMER/RESTAURANT: Can only view own profile
    """
    customer = await service.get_customer_by_id(customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    rbac = RBACService(rbac_context.role)
    if not rbac.can_view_customer(customer.user_id, rbac_context.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this customer",
        )

    logger.info(
        f"Retrieved customer | id={customer_id} | requester_role={rbac_context.role}"
    )
    return customer


@app.get(
    "/customers",
    response_model=CustomerListOut,
    tags=["Customers"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)
async def list_customers(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    rbac_context: Annotated[RBACContext, Depends(get_rbac_context)] = None,
    service: Annotated[CustomerService, Depends(get_customer_service)] = None,
) -> CustomerListOut:
    """
    List all customers with pagination.
    - ADMIN only
    """
    customers, total = await service.list_customers(skip=skip, limit=limit)
    logger.info(f"Listed customers | skip={skip} | limit={limit} | total={total}")
    return CustomerListOut(customers=customers, total=total)


@app.patch(
    "/customers/{user_id}",
    response_model=CustomerOut,
    tags=["Customers"],
)
async def update_customer_profile(
    user_id: str,
    update_data: CustomerUpdate,
    rbac_context: Annotated[RBACContext, Depends(get_rbac_context)],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerOut:
    """
    Update customer profile.
    - ADMIN: Can update any customer
    - CUSTOMER/RESTAURANT: Can only update own profile
    """
    rbac = RBACService(rbac_context.role)

    if not rbac.can_update_customer(user_id, rbac_context.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this customer",
        )

    customer = await service.update_customer(user_id, update_data)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    logger.info(
        f"Updated customer profile | user_id={user_id} | requester_role={rbac_context.role}"
    )
    return customer


@app.delete(
    "/customers/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Customers"],
)
async def delete_customer_profile(
    user_id: str,
    rbac_context: Annotated[RBACContext, Depends(get_rbac_context)],
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> None:
    """
    Delete customer profile.
    - ADMIN only
    """
    rbac = RBACService(rbac_context.role)

    if not rbac.can_delete_customer(user_id, rbac_context.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete customer profiles",
        )

    deleted = await service.delete_customer(user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    logger.info(f"Deleted customer profile | user_id={user_id}")


# ============================================================================
# INTERNAL SERVICE ENDPOINTS (for API Gateway / other microservices)
# ============================================================================


@app.get(
    "/internal/customers/{user_id}",
    response_model=CustomerOut,
    tags=["Internal"],
)
async def get_customer_internal(
    user_id: str,
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerOut:
    """
    Internal endpoint for other microservices to fetch customer by user_id.
    No RBAC required — accessible via internal service-to-service calls.
    """
    customer = await service.get_customer_by_user_id(user_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    logger.info(f"Internal: Retrieved customer | user_id={user_id}")
    return customer


@app.post(
    "/internal/customers/verify/{user_id}",
    tags=["Internal"],
)
async def verify_customer_exists(
    user_id: str,
    service: Annotated[CustomerService, Depends(get_customer_service)],
) -> dict[str, bool]:
    """
    Internal endpoint to verify if customer profile exists.
    Used by other microservices (Order Service, etc.).
    """
    customer = await service.get_customer_by_user_id(user_id)
    exists = customer is not None
    logger.info(f"Internal: Verified customer | user_id={user_id} | exists={exists}")
    return {"exists": exists}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service_port,
        reload=True,
    )
