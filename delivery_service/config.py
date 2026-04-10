from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # ------Loading env file-------
    model_config = SettingsConfigDict(env_file=(".env", "../../.env"), env_file_encoding="utf-8", extra="ignore")

    # --------------MongoDB connection--------------------
    mongodb_uri: str = "mongodb://localhost:27017/"
    mongodb_user: str | None = None
    mongodb_password: str | None = None
    mongodb_cluster_host: str | None = None
    mongodb_db_name: str = "delivery_db"
    
    # ---------------Service Configuration---------------------
    service_name: str = "Delivery Service"
    service_port: int = 8006
    order_service_url: str = "http://localhost:8008"

    def get_mongodb_connection_uri(self) -> str:
        host = (self.mongodb_cluster_host or "").strip()
        user = (self.mongodb_user or "").strip()
        if host and user and self.mongodb_password is not None:
            u = quote_plus(user)
            p = quote_plus(self.mongodb_password)
            return f"mongodb+srv://{u}:{p}@{host}/?retryWrites=true&w=majority"
        return self.mongodb_uri


settings = Settings()

MONGODB_URI = settings.get_mongodb_connection_uri()
ORDER_SERVICE_URL = settings.order_service_url

DATABASE_NAME = "delivery_db"
COLLECTION_NAME = "deliveries"