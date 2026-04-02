# API Gateway

Single entry point (`http://127.0.0.1:8001`) for all microservices.

## Service Routing

All requests are forwarded transparently to the appropriate service:

| Prefix | Service | Port | Purpose |
|--------|---------|------|---------|
| `/auth` | Authentication Service | 8002 | User login, register, JWT |
| `/customer` | Customer Service | 8003 | User profiles, RBAC |
| `/restaurant` | Restaurant Service | 8005 | Restaurant management |
| `/menu` | Menu Service | 8007 | Menu items, categories |
| `/order` | Order Service | 8008 | Cart, checkout, orders |
| `/delivery` | Delivery Service | 8009 | Driver assignment, tracking |
| `/feedback` | Feedback Service | 8010 | Ratings, reviews, comments |

## Run the Gateway

```powershell
cd "C:\Users\DELL\OneDrive\Documents\MTITI A\Online-Ordering-System"
.venv\Scripts\Activate.ps1
python -m uvicorn api_gateway.main:app --host 127.0.0.1 --port 8001 --reload
```

## Usage Examples

```bash
# Auth: http://127.0.0.1:8001/auth/register
curl -X POST http://127.0.0.1:8001/auth/register

# Menu: http://127.0.0.1:8001/menu
curl http://127.0.0.1:8001/menu

# Order: http://127.0.0.1:8001/order/cart
curl http://127.0.0.1:8001/order/cart

# Customer: http://127.0.0.1:8001/customer/me
curl http://127.0.0.1:8001/customer/me

# Restaurant: http://127.0.0.1:8001/restaurant
curl http://127.0.0.1:8001/restaurant

# Delivery: http://127.0.0.1:8001/delivery
curl http://127.0.0.1:8001/delivery

# Feedback: http://127.0.0.1:8001/feedback
curl http://127.0.0.1:8001/feedback
```

## Design

- **No Authentication/Authorization**: Pure passthrough proxy (services handle their own auth if needed).
- **No Data Transformation**: Requests and responses forwarded as-is.
- **Service Independence**: Services run on separate ports and can be stopped/started independently.
- **Transparent Routing**: Path-based routing to upstream services.

## Ensure Services Are Running

Before using the gateway, start all services:

```powershell
# Terminal 1: Auth Service (8002)
python -m uvicorn auth_service.main:app --port 8002

# Terminal 2: Customer Service (8003)
python -m uvicorn customer_service.main:app --port 8003

# Terminal 3: Restaurant Service (8005)
python -m uvicorn restaurant_service.main:app --port 8005

# Terminal 4: Menu Service (8007)
python -m uvicorn menu_service.main:app --port 8007

# Terminal 5: Order Service (8008)
python -m uvicorn order_service.main:app --port 8008

# Terminal 6: Delivery Service (8009)
python -m uvicorn delivery_service.main:app --port 8009

# Terminal 7: Feedback Service (8010)
python -m uvicorn feedback_service.main:app --port 8010

# Terminal 8: API Gateway (8001)
python -m uvicorn api_gateway.main:app --host 127.0.0.1 --port 8001
```

Or use a script/docker-compose to orchestrate all services.
