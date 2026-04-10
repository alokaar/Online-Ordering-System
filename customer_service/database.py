"""Database Connection and Utilities for Customer Service"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import InvalidURI

from .config import settings

logger = logging.getLogger(__name__)


class Database:
    client: AsyncIOMotorClient | None = None
    database: AsyncIOMotorDatabase | None = None


db_state = Database()


async def get_database() -> AsyncIOMotorDatabase:
    """Get the MongoDB database connection."""
    if db_state.database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Database unavailable. Install/start MongoDB on localhost:27017 "
                "(or set MONGODB_URI) and restart the service."
            ),
        )
    return db_state.database


def is_database_connected() -> bool:
    """Check if database is connected."""
    return db_state.database is not None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage database connection lifecycle."""
    uri = settings.get_mongodb_connection_uri()
    try:
        client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
    except InvalidURI as e:
        logger.warning("Invalid MongoDB URI (check credentials / encoding): %s", e)
        yield
        return

    try:
        await client.admin.command("ping")
        db_state.client = client
        
        db_name = "customer_db"
        db_state.database = client[db_name]

        # Create indexes
        await db_state.database.customers.create_index("email", unique=True)
        await db_state.database.customers.create_index("user_id", unique=True)

        logger.info("Customer Service: MongoDB connected (database=%s)", db_name)
    except Exception as e:
        logger.warning(
            "Customer Service: MongoDB not reachable — starting without DB. (%s)",
            e,
        )
        client.close()
        db_state.client = None
        db_state.database = None

    yield

    if db_state.client is not None:
        db_state.client.close()
        db_state.client = None
        db_state.database = None
        logger.info("Customer Service: MongoDB connection closed")
