Online Food Ordering — microservice folders (IT4020)

services/auth_service        — User accounts, JWT login (map your existing root app/ here when you split).
services/restaurant_service  — Restaurants, locations, hours.
services/menu_service        — Menu items, categories, prices.
services/order_service       — Cart, checkout, order status.
services/api_gateway         — Single entry URL; routes to the services above.

Root app/ + main.py          — Current monolith until you move code into services/*.

Each service can be its own small FastAPI project: main.py, requirements.txt, own port.
Gateway proxies paths like /auth/*, /menu/* to those ports.
