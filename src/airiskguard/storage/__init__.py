"""Storage backends for airiskguard."""

from airiskguard.storage.base import StorageBackend
from airiskguard.storage.json_file import JSONFileStorage
from airiskguard.storage.memory import MemoryStorage
from airiskguard.storage.sqlite import SQLiteStorage

__all__ = [
    "JSONFileStorage",
    "MemoryStorage",
    "PostgreSQLStorage",
    "RedisStorage",
    "SQLiteStorage",
    "StorageBackend",
]


def __getattr__(name: str):  # lazy imports to avoid hard deps
    if name == "PostgreSQLStorage":
        from airiskguard.storage.postgres import PostgreSQLStorage
        return PostgreSQLStorage
    if name == "RedisStorage":
        from airiskguard.storage.redis import RedisStorage
        return RedisStorage
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
