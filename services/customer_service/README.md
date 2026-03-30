# Customer Service Microservice

Manages user customer profiles with **Role-Based Access Control (RBAC)** for the Online Food Ordering System.

## Overview

- **Port:** 8003 (direct access) / 8000 via API Gateway
- **Database:** MongoDB (async Motor)
- **Authentication:** JWT tokens (validated by API Gateway)
- **Authorization:** RBAC via headers from Gateway

## Structure

```
customer_service/
├── main.py          # FastAPI app, routes, and endpoint handlers
├── models.py        # Pydantic models (CustomerOut, CustomerCreate, etc.)
├── service.py       # Business logic (CustomerService) + RBAC logic
├── config.py        # Configuration (MongoDB, JWT settings)
├── database.py      # Database connection, lifespan management
└── __init__.py
```

## Setup & Running

### 1. Install Dependencies (if not already done)

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

The service reads from `.env` (root project directory):

```env
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/food_ordering
JWT_SECRET_KEY=your-secret-key
```

### 3. Run the Service

```bash
# Direct (development)
cd services/customer_service
python -m uvicorn main:app --port 8003 --reload

# Or from project root
uvicorn services.customer_service.main:app --port 8003 --reload
```

### 4. Access API Documentation

- **Swagger UI:** http://localhost:8003/docs
- **ReDoc:** http://localhost:8003/redoc

---

## API Endpoints

### Public Endpoints (Require JWT + Headers from Gateway)

#### GET `/health`

Service and database health status.

**Response:**

```json
{
  "service": "Customer Service",
  "status": "running",
  "database": "connected"
}
```

---

#### POST `/customers`

Create a new customer profile.

**Headers (from Gateway):**

```
X-User-ID: 507f1f77bcf86cd799439011
X-User-Email: user@example.com
X-User-Role: customer
```

**Request Body:**

```json
{
  "user_id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "address": "123 Main St, City"
}
```

**Response:** `201 Created`

```json
{
  "id": "507f1f77bcf86cd799439012",
  "user_id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "address": "123 Main St, City",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**RBAC Rules:**
- `ADMIN`: Can create for any user
- `CUSTOMER/RESTAURANT`: Can only create for themselves
- `GUEST`: Denied ❌

---

#### GET `/customers/me`

Get current user's customer profile.

**Headers (from Gateway):**

```
X-User-ID: 507f1f77bcf86cd799439011
X-User-Email: user@example.com
X-User-Role: customer
```

**Response:** `200 OK`

Returns the authenticated user's customer profile.

---

#### GET `/customers/{customer_id}`

Get customer by ID.

**RBAC Rules:**
- `ADMIN`: Can view any customer
- `CUSTOMER/RESTAURANT`: Can only view own profile
- `GUEST`: Denied ❌

**Response:** `200 OK` or `403 Forbidden`

---

#### GET `/customers`

List all customers (paginated). **ADMIN ONLY**

**Query Parameters:**

- `skip` (int, default: 0): Number of records to skip
- `limit` (int, default: 10, max: 100): Number of records to return

**Response:** `200 OK`

```json
{
  "customers": [
    {
      "id": "507f1f77bcf86cd799439012",
      "user_id": "507f1f77bcf86cd799439011",
      "email": "user@example.com",
      "full_name": "John Doe",
      "phone": "+1234567890",
      "address": "123 Main St, City",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 42
}
```

**RBAC:** `ADMIN` only

---

#### PATCH `/customers/{user_id}`

Update customer profile.

**Request Body:**

```json
{
  "full_name": "Jane Doe",
  "phone": "+9876543210",
  "address": "456 Oak Ave, City"
}
```

**Response:** `200 OK`

**RBAC Rules:**
- `ADMIN`: Can update any customer
- `CUSTOMER/RESTAURANT`: Can only update own profile
- `GUEST`: Denied ❌

---

#### DELETE `/customers/{user_id}`

Delete customer profile. **ADMIN ONLY**

**Response:** `204 No Content`

---

### Internal Service Endpoints (Service-to-Service)

#### GET `/internal/customers/{user_id}`

Get customer by user ID (no RBAC required).

Used by Order Service, Payment Service, etc. to fetch customer details.

**Response:**

```json
{
  "id": "507f1f77bcf86cd799439012",
  "user_id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "full_name": "John Doe",
  "phone": "+1234567890",
  "address": "123 Main St, City",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

---

#### POST `/internal/customers/verify/{user_id}`

Verify if customer profile exists.

**Response:**

```json
{
  "exists": true
}
```

---

## Role-Based Access Control (RBAC)

The service implements RBAC via the **`RBACService`** class and **`RBACContext`** dependency:

### User Roles

```python
class UserRole(Enum):
    ADMIN = "admin"           # Full access to all operations
    RESTAURANT = "restaurant" # Can manage own restaurant data
    CUSTOMER = "customer"     # Can manage own profile
    GUEST = "guest"           # Limited read-only access
```

### How RBAC Works

1. **Gateway Sends Headers:**

```
X-User-ID: 507f1f77bcf86cd799439011
X-User-Email: user@example.com
X-User-Role: admin
```

2. **Service Extracts Role:**

```python
@app.get("/customers")
async def list_customers(
    rbac_context: Annotated[RBACContext, Depends(get_rbac_context)]
):
    # rbac_context.role == UserRole.ADMIN
```

3. **Enforce Authorization:**

```python
rbac = RBACService(rbac_context.role)

# Check if user can perform action
if not rbac.can_view_customer(target_user_id, rbac_context.user_id):
    raise HTTPException(status_code=403, detail="Not authorized")
```

### RBAC Methods

| Method | ADMIN | RESTAURANT | CUSTOMER | GUEST |
|--------|-------|-----------|----------|-------|
| `can_view_customer()` | ✅ Any | ✅ Own | ✅ Own | ❌ |
| `can_update_customer()` | ✅ Any | ✅ Own | ✅ Own | ❌ |
| `can_delete_customer()` | ✅ Any | ❌ | ❌ | ❌ |
| `can_list_customers()` | ✅ | ❌ | ❌ | ❌ |

---

## Error Responses

### 401 Unauthorized (Missing Headers)

```json
{
  "detail": "Missing authentication headers from Gateway"
}
```

### 403 Forbidden (Insufficient Permissions)

```json
{
  "detail": "Not authorized to view this customer"
}
```

### 404 Not Found

```json
{
  "detail": "Customer not found"
}
```

### 409 Conflict (Duplicate Profile)

```json
{
  "detail": "Customer profile already exists for this user"
}
```

### 503 Service Unavailable (DB Error)

```json
{
  "detail": "Database unavailable..."
}
```

---

## Integration with API Gateway

### Gateway Responsibilities

1. **Validate JWT token** from client
2. **Extract claims** (user_id, email, role)
3. **Pass as headers** to Customer Service:

```
X-User-ID: <user_id>
X-User-Email: <email>
X-User-Role: <role>
```

4. **Route requests:**

```
POST /api/v1/customers  →  http://localhost:8003/customers
GET  /api/v1/customers/{id}  →  http://localhost:8003/customers/{id}
```

### Example Gateway Integration

```python
# In API Gateway router
@app.post("/api/v1/customers", tags=["Gateway"])
async def create_customer_via_gateway(
    current_user: User = Depends(get_current_user),
    customer_data: CustomerCreate = None,
):
    headers = {
        "X-User-ID": current_user.id,
        "X-User-Email": current_user.email,
        "X-User-Role": current_user.role,
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8003/customers",
            json=customer_data.model_dump(),
            headers=headers,
        )
    return response.json()
```

---

## Development Notes

### Testing

To test the service locally without the Gateway, use curl with headers:

```bash
# Create customer (as ADMIN)
curl -X POST http://localhost:8003/customers \
  -H "X-User-ID: user123" \
  -H "X-User-Email: user@example.com" \
  -H "X-User-Role: admin" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "email": "user@example.com",
    "full_name": "John Doe"
  }'

# List customers (ADMIN only)
curl -X GET http://localhost:8003/customers \
  -H "X-User-ID: admin1" \
  -H "X-User-Email: admin@example.com" \
  -H "X-User-Role: admin"

# Attempt as CUSTOMER (should fail)
curl -X GET http://localhost:8003/customers \
  -H "X-User-ID: user123" \
  -H "X-User-Email: user@example.com" \
  -H "X-User-Role: customer"
# Response: 403 Forbidden
```

### Logging

Service logs to console with INFO level. Key events:

- Database connection status
- Profile creation/update/delete
- Authorization violations
- Internal service calls

### Database Indexes

Automatically created on startup:

- `email` (unique)
- `user_id` (unique)

---

## Next Steps

1. **Add Validation:** Implement email verification, phone number validation
2. **Add Caching:** Cache customer profiles with Redis
3. **Add Audit Logging:** Log all profile changes with timestamps and user IDs
4. **Add Soft Deletes:** Mark deleted profiles as inactive instead of hard delete
5. **Add Events:** Publish `customer.created`, `customer.updated` events to message queue

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Motor (Async MongoDB) Docs](https://motor.readthedocs.io/)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)
- [Role-Based Access Control](https://en.wikipedia.org/wiki/Role-based_access_control)
