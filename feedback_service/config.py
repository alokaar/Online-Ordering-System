"""Feedback Service Configuration"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Service Configuration
    service_name: str = "Feedback Service"
    service_port: int = 8004
    
    # Database Configuration (MongoDB)
    mongodb_uri: str = "mongodb://localhost:27017/"
    mongodb_db_name: str = "food_ordering"
    
    # Service Integration URLs
    auth_service_url: str = "http://localhost:8000"  # Auth Service port
    customer_service_url: str = "http://localhost:8003"  # Customer Service port
    order_service_url: str = "http://localhost:8002"  # Order Service port
    restaurant_service_url: str = "http://localhost:8006"  # Restaurant Service port (placeholder)
    
    # Security Configuration
    gateway_secret: str = "super-secret-key-123"
    
    # Feature Flags
    # ===================================
    # TO USE MONGODB:
    #   1. Start MongoDB: mongod --dbpath "C:\data\db" (Windows) or mongod (Linux/Mac)
    #   2. Change this to: use_mock_database: bool = False
    #   3. Restart the feedback service
    # ===================================
    use_mock_database: bool = False  # Set to False to use real MongoDB


settings = Settings()
