"""Auth Service Configuration"""
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../../.env"), env_file_encoding="utf-8", extra="ignore")

    # MongoDB connection (shared with API Gateway)
    mongodb_uri: str = "mongodb://localhost:27017/"
    mongodb_user: str | None = None
    mongodb_password: str | None = None
    mongodb_cluster_host: str | None = None
    mongodb_db_name: str = "food_ordering"
    
    # JWT Configuration
    jwt_secret_key: str = "dev-only-change-me-use-env-JWT_SECRET_KEY"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    
    # Service Configuration
    service_name: str = "Auth Service"
    service_port: int = 8000
    customer_service_url: str = "http://localhost:8003"

    def get_mongodb_connection_uri(self) -> str:
        """Build Atlas SRV URI with RFC 3986–safe credentials, or use mongodb_uri for localhost."""
        host = (self.mongodb_cluster_host or "").strip()
        user = (self.mongodb_user or "").strip()
        if host and user and self.mongodb_password is not None:
            u = quote_plus(user)
            p = quote_plus(self.mongodb_password)
            return f"mongodb+srv://{u}:{p}@{host}/?retryWrites=true&w=majority"
        return self.mongodb_uri


settings = Settings()
