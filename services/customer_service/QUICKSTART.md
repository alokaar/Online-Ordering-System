"""
QUICK START GUIDE - Customer Service Microservice

This boilerplate provides a complete Customer Service microservice with RBAC.
"""

# ============================================================================
# FILES CREATED
# ============================================================================

"""
services/customer_service/
├── main.py              # FastAPI app with all endpoints
├── models.py            # Pydantic models (Customer, RBAC roles, responses)
├── service.py           # Business logic + RBAC implementation
├── config.py            # Configuration (MongoDB, JWT, service settings)
├── database.py          # Async MongoDB connection + lifespan
├── __init__.py
├── README.md            # Full documentation
├── .env.example         # Environment variables template
└── QUICKSTART.md        # This file
"""

# ============================================================================
# 4-FILE STRUCTURE EXPLAINED
# ============================================================================

"""
1. main.py
   - FastAPI application setup
   - Route definitions (endpoints)
   - Endpoint handlers
   - Error handling
   
2. models.py
   - Pydantic schemas for request/response validation
   - UserRole enum (ADMIN, RESTAURANT, CUSTOMER, GUEST)
   - Customer model, RBACContext model
   
3. service.py
   - CustomerService: Database operations (CRUD)
   - RBACService: Permission checking logic
   - Authentication dependencies: get_rbac_context()
   - Authorization decorators: require_role()
   
4. database.py
   - MongoDB connection management (async)
   - Database lifecycle (startup/shutdown)
   - Dependency injection: get_database()
"""

# ============================================================================
# KEY FEATURES
# ============================================================================

"""
1. ROLE-BASED ACCESS CONTROL (RBAC)
   ✓ Four user roles: ADMIN, RESTAURANT, CUSTOMER, GUEST
   ✓ Row-level security (users can only access own data)
   ✓ Different permissions per endpoint
   ✓ Easy to extend with custom roles

2. JWT AUTHENTICATION
   ✓ Token validation via headers from API Gateway
   ✓ Headers: X-User-ID, X-User-Email, X-User-Role
   ✓ No token validation in service (Gateway responsibility)

3. ASYNC DATABASE OPERATIONS
   ✓ Motor (async MongoDB driver)
   ✓ Non-blocking I/O
   ✓ Automatic connection management

4. PROFESSIONAL LOGGING
   ✓ Request logging with action context
   ✓ Error tracking
   ✓ Database connection status

5. HEALTH CHECKS
   ✓ /health endpoint for monitoring
   ✓ Database connectivity status
   ✓ Service readiness checks
"""

# ============================================================================
# QUICK START
# ============================================================================

"""
STEP 1: Install Dependencies (if needed)
  cd /path/to/project
  pip install -r requirements.txt

STEP 2: Verify .env Configuration
  Make sure .env in project root has:
    MONGODB_URI=mongodb://localhost:27017/
    JWT_SECRET_KEY=replace-with-a-long-random-secret

STEP 3: Start MongoDB
  # Windows
  mongod
  
  # Or use MongoDB Atlas (cloud)

STEP 4: Run the Service
  cd services/customer_service
  python -m uvicorn main:app --port 8003 --reload
  
  # Or from project root:
  uvicorn services.customer_service.main:app --port 8003 --reload

STEP 5: Open Swagger UI
  http://localhost:8003/docs

STEP 6: Test the Service
  See "TESTING" section below
"""

# ============================================================================
# TESTING WITHOUT API GATEWAY
# ============================================================================

"""
All endpoints require headers from the Gateway:
  X-User-ID: user_id_here
  X-User-Email: user_email_here
  X-User-Role: admin|restaurant|customer|guest

Use curl to test locally:

TEST 1: Health Check
  curl http://localhost:8003/health

TEST 2: Create Customer (as ADMIN)
  curl -X POST http://localhost:8003/customers \
    -H "X-User-ID: admin_001" \
    -H "X-User-Email: admin@example.com" \
    -H "X-User-Role: admin" \
    -H "Content-Type: application/json" \
    -d '{
      "user_id": "user_123",
      "email": "john@example.com",
      "full_name": "John Doe",
      "phone": "+1234567890",
      "address": "123 Main St"
    }'

TEST 3: Get Own Profile
  curl http://localhost:8003/customers/me \
    -H "X-User-ID: user_123" \
    -H "X-User-Email: john@example.com" \
    -H "X-User-Role: customer"

TEST 4: List All Customers (ADMIN ONLY)
  curl http://localhost:8003/customers \
    -H "X-User-ID: admin_001" \
    -H "X-User-Email: admin@example.com" \
    -H "X-User-Role: admin"

TEST 5: Try as CUSTOMER (should fail - 403)
  curl http://localhost:8003/customers \
    -H "X-User-ID: user_123" \
    -H "X-User-Email: john@example.com" \
    -H "X-User-Role: customer"

TEST 6: Update Profile
  curl -X PATCH http://localhost:8003/customers/user_123 \
    -H "X-User-ID: user_123" \
    -H "X-User-Email: john@example.com" \
    -H "X-User-Role: customer" \
    -H "Content-Type: application/json" \
    -d '{
      "full_name": "Jane Doe",
      "phone": "+9999999999"
    }'

TEST 7: Delete Profile (ADMIN ONLY)
  curl -X DELETE http://localhost:8003/customers/user_123 \
    -H "X-User-ID: admin_001" \
    -H "X-User-Email: admin@example.com" \
    -H "X-User-Role: admin"
"""

# ============================================================================
# RBAC PERMISSION MATRIX
# ============================================================================

"""
Endpoint               | ADMIN | RESTAURANT | CUSTOMER | GUEST
----------------------|-------|-----------|----------|-------
POST /customers       | ✅    | ✅        | ✅       | ❌
GET /customers/me     | ✅    | ✅        | ✅       | ❌
GET /customers/{id}   | ✅    | ✅/own    | ✅/own   | ❌
GET /customers (list) | ✅    | ❌        | ❌       | ❌
PATCH /customers/{id} | ✅    | ✅/own    | ✅/own   | ❌
DELETE /customers/{id}| ✅    | ❌        | ❌       | ❌

Legend:
  ✅     = Full access
  ✅/own = Can only access own data
  ❌     = No access (403 Forbidden)
"""

# ============================================================================
# INTEGRATION WITH API GATEWAY
# ============================================================================

"""
The API Gateway should:

1. Validate JWT token from client
2. Extract user info and role from token payload
3. Forward request to Customer Service with headers:
   - X-User-ID: extracted_user_id
   - X-User-Email: extracted_user_email
   - X-User-Role: extracted_user_role

Example Gateway Implementation:
  from fastapi import Depends
  import httpx
  
  @app.post("/api/v1/customers")
  async def create_customer_gateway(
      customer_data: CustomerCreate,
      current_user: User = Depends(get_current_user),
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
"""

# ============================================================================
# EXTENDING THE SERVICE
# ============================================================================

"""
Add New Endpoint with RBAC:

  from fastapi import APIRouter, Depends
  
  @app.get("/customers/stats", tags=["Analytics"])
  async def get_customer_stats(
      rbac_context: Annotated[RBACContext, Depends(get_rbac_context)],
      service: Annotated[CustomerService, Depends(get_customer_service)],
      dependencies=[Depends(require_role(UserRole.ADMIN))],
  ):
      # Only ADMIN can access this
      customers, total = await service.list_customers()
      return {
          "total_customers": total,
          "accessed_by_role": rbac_context.role,
      }

Add Custom Permission:

  class RBACService:
      def can_export_data(self) -> bool:
          \"\"\"Only ADMIN can export customer data\"\"\"
          return self.role == UserRole.ADMIN
"""

# ============================================================================
# FILE STRUCTURE AFTER SETUP
# ============================================================================

"""
Online-Ordering-System/
├── main.py                  # Main API Gateway
├── requirements.txt
├── .env                     # Configuration
├── app/
│   ├── auth.py
│   ├── config.py
│   ├── database.py
│   ├── schemas.py
│   └── routers/
├── services/
│   ├── customer_service/    👈 YOUR SERVICE
│   │   ├── main.py          # FastAPI app + routes
│   │   ├── models.py        # Pydantic schemas
│   │   ├── service.py       # Business logic + RBAC
│   │   ├── config.py        # Config settings
│   │   ├── database.py      # DB connection
│   │   ├── __init__.py
│   │   ├── README.md        # Full documentation
│   │   ├── .env.example     # Env template
│   │   └── QUICKSTART.md    # This file
│   ├── order_service/
│   └── menu_service/
└── docs/
"""

# ============================================================================
# NEXT STEPS
# ============================================================================

"""
1. Read the full README.md for detailed API documentation
2. Test the service using curl commands (see TESTING section)
3. Integrate with API Gateway (use Gateway Integration example)
4. Configure MongoDB connection (if using Atlas)
5. Add more routes/endpoints as needed
6. Implement service-to-service calls (e.g., Order Service → Customer Service)
7. Add unit tests (pytest)
8. Deploy to production with environment variables
"""

# ============================================================================
# COMMON ISSUES
# ============================================================================

"""
Issue: 503 Service Unavailable (Database connection failed)
Solution:
  - Check MongoDB is running: mongod or MongoDB Compass
  - Verify MONGODB_URI in .env
  - Check network connectivity to MongoDB

Issue: 401 Unauthorized (Missing headers)
Solution:
  - Ensure API Gateway sends X-User-* headers
  - Use correct header names (case-sensitive in HTTP spec)
  - Test with curl to verify headers

Issue: 403 Forbidden (Permission denied)
Solution:
  - Check user role matches endpoint requirements
  - Verify RBAC rules in service.py
  - Use correct role value (admin, customer, restaurant, guest)

Issue: Module not found errors
Solution:
  - Install requirements: pip install -r requirements.txt
  - Run from correct directory
  - Use proper Python path: python -m uvicorn ...
"""

# ============================================================================
# SUPPORT FILES
# ============================================================================

print("✅ Customer Service Boilerplate Generated!")
print("📁 Location: /services/customer_service/")
print("📖 Documentation: README.md")
print("🚀 Start: uvicorn services.customer_service.main:app --port 8003")
print("🌐 Swagger: http://localhost:8003/docs")
print("\nHappy coding! 🎉")
