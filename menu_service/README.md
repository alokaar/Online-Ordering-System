# Menu Service

Standalone microservice for managing menu items.

- Start with `python main.py` (or `uvicorn services.menu_service.main:app --reload --port 8002`).
- Exposes `/menu` endpoints for CRUD.
- Uses MongoDB collection `menu_items`.
