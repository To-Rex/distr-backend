import json
import threading
from pathlib import Path
from typing import Any, Callable, Optional


class JsonDB:
    _locks: dict[str, threading.Lock] = {}
    _global_lock = threading.Lock()

    @classmethod
    def _get_lock(cls, file_path: Path) -> threading.Lock:
        key = str(file_path)
        with cls._global_lock:
            if key not in cls._locks:
                cls._locks[key] = threading.Lock()
            return cls._locks[key]

    @classmethod
    def read(cls, file_path: Path) -> list[dict[str, Any]]:
        lock = cls._get_lock(file_path)
        with lock:
            if not file_path.exists():
                return []
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []

    @classmethod
    def write(cls, file_path: Path, data: list[dict[str, Any]]) -> None:
        lock = cls._get_lock(file_path)
        with lock:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def read_one(
        cls, file_path: Path, predicate: Callable[[dict], bool]
    ) -> Optional[dict[str, Any]]:
        records = cls.read(file_path)
        for record in records:
            if predicate(record):
                return record
        return None

    @classmethod
    def insert(cls, file_path: Path, record: dict[str, Any]) -> dict[str, Any]:
        records = cls.read(file_path)
        records.append(record)
        cls.write(file_path, records)
        return record

    @classmethod
    def update(
        cls, file_path: Path, predicate: Callable[[dict], bool], updates: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        records = cls.read(file_path)
        for i, record in enumerate(records):
            if predicate(record):
                records[i].update(updates)
                cls.write(file_path, records)
                return records[i]
        return None

    @classmethod
    def delete(cls, file_path: Path, predicate: Callable[[dict], bool]) -> bool:
        records = cls.read(file_path)
        original_len = len(records)
        records = [r for r in records if not predicate(r)]
        if len(records) < original_len:
            cls.write(file_path, records)
            return True
        return False
