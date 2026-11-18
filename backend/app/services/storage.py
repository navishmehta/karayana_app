"""File storage for uploaded media. Local disk now; an S3-compatible driver can be added behind the same API."""

from functools import lru_cache
from pathlib import Path
from typing import Protocol

from app.core.config import get_settings


class Storage(Protocol):
    def save(self, path: str, content: bytes) -> None: ...
    def delete(self, *paths: str | None) -> None: ...
    def url(self, path: str | None) -> str | None: ...


class LocalStorage:
    def __init__(self, root: str, base_url: str) -> None:
        self.root = Path(root).resolve()
        self.base_url = base_url.rstrip("/")

    def _full_path(self, path: str) -> Path:
        full = (self.root / path).resolve()
        if not full.is_relative_to(self.root):  # never write outside the media folder
            raise ValueError("Invalid media path")
        return full

    def save(self, path: str, content: bytes) -> None:
        full = self._full_path(path)
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_bytes(content)

    def delete(self, *paths: str | None) -> None:
        for path in filter(None, paths):
            self._full_path(path).unlink(missing_ok=True)

    def exists(self, path: str) -> bool:
        return self._full_path(path).exists()

    def url(self, path: str | None) -> str | None:
        return f"{self.base_url}/{path}" if path else None


@lru_cache
def get_storage() -> Storage:
    settings = get_settings()
    return LocalStorage(settings.media_root, settings.media_base_url)
