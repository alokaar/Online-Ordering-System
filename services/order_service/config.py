from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mongodb_uri: str = "mongodb://localhost:27017/"
    mongodb_user: str | None = None
    mongodb_password: str | None = None
    mongodb_cluster_host: str | None = None
    mongodb_db_name: str = "food_ordering"
    service_name: str = "order_service"

    def get_mongodb_connection_uri(self) -> str:
        host = (self.mongodb_cluster_host or "").strip()
        user = (self.mongodb_user or "").strip()
        if host and user and self.mongodb_password is not None:
            u = quote_plus(user)
            p = quote_plus(self.mongodb_password)
            return f"mongodb+srv://{u}:{p}@{host}/?retryWrites=true&w=majority"
        return self.mongodb_uri


settings = Settings()
