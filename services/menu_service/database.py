import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import InvalidURI

from .config import settings

logger = logging.getLogger(__name__)


class DatabaseState:
    client: AsyncIOMotorClient | None = None
    database: AsyncIOMotorDatabase | None = None


db_state = DatabaseState()


async def get_database() -> AsyncIOMotorDatabase:
    if db_state.database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable. Start MongoDB and retry.",
        )
    return db_state.database


def is_database_connected() -> bool:
    return db_state.database is not None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    uri = settings.get_mongodb_connection_uri()
    try:
        client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
    except InvalidURI as e:
        logger.error("Invalid MongoDB URI: %s", e)
        yield
        return

    try:
        await client.admin.command("ping")
        db_state.client = client
        db_state.database = client[settings.mongodb_db_name]
        await db_state.database.menu_items.create_index("name")
        logger.info("MongoDB connected (database=%s)", settings.mongodb_db_name)
    except Exception as e:
        logger.warning("MongoDB not reachable: %s", e)
        client.close()
        db_state.client = None
        db_state.database = None

    yield

    if db_state.client is not None:
        db_state.client.close()
        db_state.client = None
        db_state.database = None
