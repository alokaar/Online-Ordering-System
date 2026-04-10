# Order Service

Standalone microservice for cart and order processing.

- Start with `python main.py` (or `uvicorn services.order_service.main:app --reload --port 8004`).
- Exposes `/orders/cart` and `/orders` endpoints.
- Requires `X-User-ID` header to identify the user.
- Uses MongoDB collection `orders` and reads `menu_items` for price checks.
