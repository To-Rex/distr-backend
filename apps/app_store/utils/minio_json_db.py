import threading
from typing import Any, Callable, Optional

from apps.app_store.services.minio_storage import get_json, put_json


class MinioJsonDB:
    _locks: dict[str, threading.Lock] = {}
    _global_lock = threading.Lock()

    @classmethod
    def _get_lock(cls, object_key: str) -> threading.Lock:
        with cls._global_lock:
            if object_key not in cls._locks:
                cls._locks[object_key] = threading.Lock()
            return cls._locks[object_key]

    @classmethod
    def read(cls, object_key: str) -> list[dict[str, Any]]:
        lock = cls._get_lock(object_key)
        with lock:
            return get_json(object_key)

    @classmethod
    def write(cls, object_key: str, data: list[dict[str, Any]]) -> None:
        lock = cls._get_lock(object_key)
        with lock:
            put_json(object_key, data)

    @classmethod
    def read_one(
        cls, object_key: str, predicate: Callable[[dict], bool]
    ) -> Optional[dict[str, Any]]:
        records = cls.read(object_key)
        for record in records:
            if predicate(record):
                return record
        return None

    @classmethod
    def insert(cls, object_key: str, record: dict[str, Any]) -> dict[str, Any]:
        records = cls.read(object_key)
        records.append(record)
        cls.write(object_key, records)
        return record

    @classmethod
    def update(
        cls, object_key: str, predicate: Callable[[dict], bool], updates: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        records = cls.read(object_key)
        for i, record in enumerate(records):
            if predicate(record):
                records[i].update(updates)
                cls.write(object_key, records)
                return records[i]
        return None

    @classmethod
    def delete(cls, object_key: str, predicate: Callable[[dict], bool]) -> bool:
        records = cls.read(object_key)
        original_len = len(records)
        records = [r for r in records if not predicate(r)]
        if len(records) < original_len:
            cls.write(object_key, records)
            return True
        return False
