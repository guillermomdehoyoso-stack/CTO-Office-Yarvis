from __future__ import annotations

import io
import os
import re
from abc import ABC, abstractmethod
from pathlib import Path
from uuid import uuid4


SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


class DocumentRepository(ABC):
    @abstractmethod
    def save(self, *, filename: str, content: bytes) -> str:
        raise NotImplementedError

    @abstractmethod
    def open(self, storage_reference: str) -> io.BytesIO:
        raise NotImplementedError

    @abstractmethod
    def exists(self, storage_reference: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete_temporary(self, storage_reference: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_metadata(self, storage_reference: str) -> dict:
        raise NotImplementedError


class LocalDocumentRepository(DocumentRepository):
    def __init__(self, root: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        base = os.path.basename(filename or "document")
        normalized = SAFE_NAME_RE.sub("_", base).strip("._")
        return normalized or "document"

    def _safe_path(self, storage_reference: str) -> Path:
        if storage_reference.startswith("/"):
            raise ValueError("invalid storage reference")
        path = (self.root / storage_reference).resolve()
        if not str(path).startswith(str(self.root.resolve())):
            raise ValueError("path traversal detected")
        return path

    def save(self, *, filename: str, content: bytes) -> str:
        safe_name = self._sanitize_filename(filename)
        ext = Path(safe_name).suffix.lower()
        internal_name = f"{uuid4().hex}{ext}"
        storage_reference = f"documents/{internal_name}"
        target = self._safe_path(storage_reference)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return storage_reference

    def open(self, storage_reference: str) -> io.BytesIO:
        path = self._safe_path(storage_reference)
        return io.BytesIO(path.read_bytes())

    def exists(self, storage_reference: str) -> bool:
        try:
            return self._safe_path(storage_reference).exists()
        except ValueError:
            return False

    def delete_temporary(self, storage_reference: str) -> None:
        path = self._safe_path(storage_reference)
        if path.exists():
            path.unlink()

    def get_metadata(self, storage_reference: str) -> dict:
        path = self._safe_path(storage_reference)
        stat = path.stat()
        return {
            "storage_reference": storage_reference,
            "byte_size": stat.st_size,
            "filename": path.name,
        }
