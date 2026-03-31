#!/usr/bin/env python
"""Test script to verify auth routes are registered"""
from services.auth_service.main import app

print("Routes registered in auth service app:")
for route in app.routes:
    if hasattr(route, 'path'):
        methods = getattr(route, 'methods', ['GET'])
        print(f"  {route.path} - {methods}")
