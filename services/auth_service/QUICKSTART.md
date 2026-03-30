# Auth Service Quick Start

## 1. Start the Service

```bash
cd services/auth_service
uvicorn main:app --port 8000 --reload
```

Service runs at: **http://localhost:8000**

## 2. Test Registration

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "password": "12345678",
    "full_name": "Demo User"
  }'
```

Response:
```json
{
  "id": "65a1b2c3d4e5f6g7h8i9j0k1",
  "email": "demo@example.com",
  "full_name": "Demo User",
  "created_at": "2024-03-30T10:00:00Z"
}
```

## 3. Test Login

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo@example.com&password=12345678"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## 4. Test Get Current User

```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer <your-token-here>"
```

## 5. Test Change Password

```bash
curl -X POST "http://localhost:8000/auth/change-password" \
  -H "Authorization: Bearer <your-token-here>" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "12345678",
    "new_password": "87654321"
  }'
```

## 6. Health Check

```bash
curl http://localhost:8000/health
```

## Documentation

- Swagger UI: **http://localhost:8000/docs**
- ReDoc: **http://localhost:8000/redoc**
