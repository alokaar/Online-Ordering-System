# Feedback Service Microservice

Customer feedback and rating system for the Online Food Ordering System.

## Features

- **Submit Feedback:** Customers can rate (1-5 stars) and review orders
- **View Reviews:** Public endpoint to view all reviews for a restaurant  
- **Average Ratings:** Automatic calculation of restaurant ratings
- **Admin Moderation:** Admins can delete inappropriate reviews
- **RBAC:** Role-based access control via API Gateway headers
- **Mock Database:** Works out-of-the-box with in-memory mock DB
- **Data Isolation:** Manages its own independent data store

## Architecture

```
feedback_service/
├── main.py          # FastAPI app and endpoints
├── models.py        # Pydantic models (FeedbackOut, etc.)
├── service.py       # Business logic + RBAC service
├── database.py      # Mock DB + MongoDB integration ready
├── config.py        # Configuration
└── __init__.py
```

## Running the Service

### Direct Start

```bash
uvicorn services.feedback_service.main:app --port 8004
```

### From Project Root

```bash
cd services/feedback_service
python -m uvicorn main:app --port 8004 --reload
```

Service will be available at: **http://localhost:8004**

## API Endpoints

### Public Endpoints (Require RBAC Headers)

#### POST `/feedbacks` - Create Feedback
**Access:** CUSTOMERS only

Request headers (from API Gateway):
```
X-User-ID: user_123
X-User-Email: customer@example.com
X-User-Role: customer
```

Request body:
```json
{
  "order_id": "order_001",
  "restaurant_id": "rest_001",
  "rating": 5,
  "review_text": "Excellent food and great service! Highly recommended."
}
```

Response (201 Created):
```json
{
  "id": "fb_001",
  "user_id": "user_123",
  "email": "customer@example.com",
  "order_id": "order_001",
  "restaurant_id": "rest_001",
  "rating": 5,
  "review_text": "Excellent food and great service! Highly recommended.",
  "created_at": "2026-03-31T10:00:00",
  "updated_at": null,
  "is_deleted": false
}
```

---

#### GET `/feedbacks/restaurant/{restaurant_id}` - Get Restaurant Reviews
**Access:** All authenticated users

Request headers:
```
X-User-ID: user_123
X-User-Email: customer@example.com
X-User-Role: customer
```

Response (200 OK):
```json
{
  "restaurant_id": "rest_001",
  "feedbacks": [
    {
      "id": "fb_001",
      "user_id": "user_001",
      "email": "customer1@example.com",
      "order_id": "order_001",
      "restaurant_id": "rest_001",
      "rating": 5,
      "review_text": "Excellent pizza! Fresh ingredients and very tasty.",
      "created_at": "2026-03-30T10:00:00",
      "updated_at": null,
      "is_deleted": false
    }
  ],
  "total": 1,
  "average_rating": 4.33
}
```

---

#### GET `/feedbacks/{feedback_id}` - Get Single Feedback
**Access:** All authenticated users

Response (200 OK): Returns single feedback object

---

#### DELETE `/feedbacks/{feedback_id}` - Delete Feedback
**Access:** ADMINS only

Request headers:
```
X-User-ID: admin_001
X-User-Email: admin@example.com
X-User-Role: admin
```

Response (204 No Content)

---

### Internal Service Endpoints

#### GET `/internal/restaurants/{restaurant_id}/average-rating`
**Access:** Other microservices (no auth required)

Response (200 OK):
```json
{
  "restaurant_id": "rest_001",
  "average_rating": 4.33,
  "feedback_count": 3
}
```

Used by:
- Restaurant Service: Display ratings on restaurant profiles
- Order Service: Recommendations based on ratings

---

#### GET `/health` - Health Check
**Access:** All authenticated users

Response (200 OK):
```json
{
  "status": "ok",
  "service": "Feedback Service",
  "database_mode": "mock"
}
```

---

## Database Setup

### Current: Mock Database (In-Memory)

The service uses an in-memory mock database for development. No MongoDB setup required!

**Location:** `database.py` → `MockDatabase` class

**Features:**
- Pre-loaded with sample data (3 example feedbacks)
- Auto-incrementing feedback IDs
- Soft delete support
- Rating aggregation

---

### Future: Real MongoDB Integration

When you're ready to use MongoDB:

1. **Environment Variable:**
   ```env
   USE_MOCK_DATABASE=false
   ```

2. **Database Selection:**
   ```python
   # In service.py
   if settings.use_mock_database:
       return MockDatabase()
   else:
       return MongoDB()  # TODO: Implement
   ```

**Ready-to-implement MongoDB features:**
- User authentication
- Order validation (check with Order Service)
- Restaurant validation (check with Restaurant Service)
- Audit logging
- Query optimization

---

## RBAC - Role-Based Access Control

### User Roles

| Role | Create | Delete | View All |
|------|--------|--------|----------|
| CUSTOMER | ✅ Own | ❌ | ✅ |
| ADMIN | ❌ | ✅ | ✅ |
| RESTAURANT | ❌ | ❌ | ✅ |
| GUEST | ❌ | ❌ | ✅ |

### How It Works

1. **API Gateway** validates JWT token
2. **Gateway** extracts: `user_id`, `email`, `role`
3. **Gateway** forwards as headers:
   ```
   X-User-ID: extracted_id
   X-User-Email: extracted_email  
   X-User-Role: extracted_role
   ```
4. **Feedback Service** extracts headers
5. **RBAC checks** control what users can do

---

## Usage Example

### 1. Register & Create Feedback

```bash
# Register user (Auth Service)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "customer@example.com",
    "password": "12345678",
    "full_name": "John Doemere"
  }'
# Returns: access_token

# Get JWT token (Login)
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=customer@example.com&password=12345678"
# Returns: JWT token

# Create feedback (via API Gateway - auto-adds headers from JWT)
curl -X POST http://localhost:8000/api/feedbacks \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "order_123",
    "restaurant_id": "rest_001",
    "rating": 5,
    "review_text": "Amazing food quality and fast delivery. Will definitely order again soon!"
  }'
```

### 2. View Restaurant Reviews

```bash
# Get all reviews for a restaurant
curl -X GET http://localhost:8000/api/feedbacks/restaurant/rest_001 \
  -H "Authorization: Bearer <jwt_token>"
```

### 3. Admin Deletes Inappropriate Review

```bash
# Admin deletes feedback
curl -X DELETE http://localhost:8000/api/feedbacks/fb_001 \
  -H "Authorization: Bearer <admin_jwt_token>"
```

---

## Testing

### Swagger UI
- **URL:** http://localhost:8004/docs
- Manual headers for testing (not needed in production)

### Curl with Manual Headers (Development)

```bash
# Create feedback (simulate CUSTOMER via headers)
curl -X POST http://localhost:8004/feedbacks \
  -H "X-User-ID: user_123" \
  -H "X-User-Email: customer@example.com" \
  -H "X-User-Role: customer" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "order_123",
    "restaurant_id": "rest_001",
    "rating": 4,
    "review_text": "Good quality food with reasonable pricing and nice service staff."
  }'

# Get reviews (CUSTOMER accessing)
curl -X GET http://localhost:8004/feedbacks/restaurant/rest_001 \
  -H "X-User-ID: user_123" \
  -H "X-User-Email: customer@example.com" \
  -H "X-User-Role: customer"

# Delete feedback (ADMIN only)
curl -X DELETE http://localhost:8004/feedbacks/fb_001 \
  -H "X-User-ID: admin_001" \
  -H "X-User-Email: admin@example.com" \
  -H "X-User-Role: admin"

# Get average rating (internal, no auth needed)
curl -X GET http://localhost:8004/internal/restaurants/rest_001/average-rating
```

---

## Integration with Other Services

### Order Service Integration (8005)

When Order Service is ready:

```python
# In database.py - Add validation
async def validate_order(self, order_id: str) -> bool:
    """Check if order exists in Order Service"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.order_service_url}/internal/orders/{order_id}"
        )
        return response.status_code == 200
```

### Restaurant Service Integration (8006)

When Restaurant Service is ready:

```python
# In service.py - Validate restaurant
async def validate_restaurant(self, restaurant_id: str) -> bool:
    """Check if restaurant exists"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{settings.restaurant_service_url}/internal/restaurants/{restaurant_id}"
        )
        return response.status_code == 200
```

---

## Configuration

### Environment Variables (`.env`)

```env
# Service
SERVICE_NAME=Feedback Service
SERVICE_PORT=8004

# Database
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=food_ordering
USE_MOCK_DATABASE=true

# Service URLs (for validation)
ORDER_SERVICE_URL=http://localhost:8005
RESTAURANT_SERVICE_URL=http://localhost:8006
```

---

## Development Notes

### Adding Real MongoDB

1. Install dependencies:
   ```bash
   pip install motor pymongo
   ```

2. Implement in `database.py`:
   ```python
   class RealDatabase:
       async def __init__(self):
           self.client = AsyncIOMotorClient(settings.mongodb_uri)
           self.db = self.client[settings.mongodb_db_name]
       
       async def create_feedback(self, ...):
           # MongoDB implementation
           pass
   ```

3. Update `get_database()` to switch based on `settings.use_mock_database`

### Next Steps

1. ✅ Mock database (DONE)
2. ⏳ Order Service integration (pending order_service code)
3. ⏳ Restaurant Service integration (pending restaurant_service code)
4. ⏳ MongoDB real database
5. ⏳ Audit logging
6. ⏳ Rate limiting
7. ⏳ Cache average ratings with Redis

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic V2](https://docs.pydantic.dev/latest/)
- [Motor - Async MongoDB](https://motor.readthedocs.io/)
