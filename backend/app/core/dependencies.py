"""
Dependency injection module for FastAPI.

Provides database connections and service instances via FastAPI's Depends().
"""

from typing import Annotated, Generator

from app.core.config import Settings, get_settings
from fastapi import Depends
from pymongo import MongoClient
from pymongo.database import Database


def get_mongo_client(
    settings: Annotated[Settings, Depends(get_settings)],
) -> Generator[MongoClient, None, None]:
    """
    Get MongoDB client instance.

    Args:
        settings: Application settings.

    Yields:
        MongoClient instance.
    """
    client = MongoClient(settings.MONGODB_URI)
    try:
        yield client
    finally:
        client.close()


def get_database(
    client: Annotated[MongoClient, Depends(get_mongo_client)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Database:
    """
    Get MongoDB database instance.

    Args:
        client: MongoDB client.
        settings: Application settings.

    Returns:
        Database instance for the fleet management database.
    """
    return client[settings.DATABASE_NAME]


# Type aliases for dependency injection
DatabaseDep = Annotated[Database, Depends(get_database)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
