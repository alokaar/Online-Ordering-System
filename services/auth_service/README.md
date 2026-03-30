# Auth Service

User authentication microservice for the Online Food Ordering System.

## Features

- User registration with email validation
- JWT-based authentication
- Password hashing with bcrypt
- Password change functionality
- Role-based access control ready

## Running the Service

```bash
# From project root
uvicorn services.auth_service.main:app --port 8000 --reload
```

The service will be available at `http://localhost:8000`

## Environment Variables

Create a `.env` file:

```
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=food_ordering
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

## API Endpoints

### Register
```bash
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "12345678",
  "full_name": "John Doe"
}
```

### Login
```bash
POST /auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=12345678
```

### Get Current User
```bash
GET /auth/me
Authorization: Bearer <token>
```

### Change Password
```bash
POST /auth/change-password
Authorization: Bearer <token>
Content-Type: application/json

{
  "current_password": "12345678",
  "new_password": "87654321"
}
```

### Health Check
```bash
GET /health
```

## Database

- Uses MongoDB (same instance as main API Gateway)
- Collections: `users`
- Index: `email` (unique)
