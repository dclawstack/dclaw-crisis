"""Object storage abstraction backed by MinIO (PRD §4).

Two backends behind one interface:
- **MinioBackend** — talks to a real MinIO / S3-compatible server.
- **InMemoryBackend** — used when `MINIO_DISABLED=true` or no endpoint is
  configured, so dev + tests don't need MinIO running. Returns a local
  pseudo-presigned URL pointing at `/api/v1/exports/local/{key}` (served by
  the export router) so the UX is the same.

Use cases shipped today:
- Legal-hold notice exports (`POST /legal-holds/{id}/export`)
- Crisis post-mortem exports (`POST /crisis/{id}/export-post-mortem`)
"""
from __future__ import annotations

import io
import logging
from datetime import timedelta
from typing import Protocol

from app.core.config import settings

logger = logging.getLogger(__name__)


class ObjectStore(Protocol):
    backend: str

    def put_text(self, key: str, text: str, content_type: str = "text/plain") -> None: ...
    def presigned_get_url(self, key: str, expires_seconds: int | None = None) -> str: ...
    def get_text(self, key: str) -> str | None: ...
    def exists(self, key: str) -> bool: ...


class InMemoryBackend:
    backend = "simulator"

    def __init__(self) -> None:
        # Class-level dict so multiple ObjectStore() calls share state (handy
        # because get-after-put across requests needs the same store).
        if not hasattr(self.__class__, "_store"):
            self.__class__._store = {}  # type: ignore[attr-defined]

    def put_text(self, key: str, text: str, content_type: str = "text/plain") -> None:
        self.__class__._store[key] = {"body": text, "content_type": content_type}  # type: ignore[attr-defined]

    def get_text(self, key: str) -> str | None:
        entry = self.__class__._store.get(key)  # type: ignore[attr-defined]
        if entry is None:
            return None
        return entry["body"]

    def exists(self, key: str) -> bool:
        return key in self.__class__._store  # type: ignore[attr-defined]

    def presigned_get_url(self, key: str, expires_seconds: int | None = None) -> str:
        # Local pseudo-presigned URL — served by `routes/exports.py` so the
        # UI flow works without a real S3-compatible server.
        return f"/api/v1/exports/local/{key}"


class MinioBackend:
    backend = "minio"

    def __init__(self) -> None:
        from minio import Minio  # local import keeps the dep optional in tests

        # Pin the region so minio-py doesn't try get_bucket_location at presign
        # time — that auto-discovery call would target the public endpoint
        # which isn't reachable from inside the backend container.
        _region = "us-east-1"

        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
            region=_region,
        )
        # Separate client whose endpoint matches the publicly-reachable host —
        # used only for presigned-URL signing so the URL is valid when a
        # browser loads it from outside the container network.
        if settings.minio_public_endpoint and settings.minio_public_endpoint != settings.minio_endpoint:
            self.signing_client = Minio(
                settings.minio_public_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure,
                region=_region,
            )
        else:
            self.signing_client = self.client
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        from minio.error import S3Error

        try:
            if not self.client.bucket_exists(settings.minio_bucket):
                self.client.make_bucket(settings.minio_bucket)
        except S3Error as exc:
            logger.warning("minio: bucket setup failed: %s", exc)

    def put_text(self, key: str, text: str, content_type: str = "text/plain") -> None:
        data = text.encode("utf-8")
        self.client.put_object(
            settings.minio_bucket,
            key,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )

    def get_text(self, key: str) -> str | None:
        from minio.error import S3Error

        try:
            obj = self.client.get_object(settings.minio_bucket, key)
        except S3Error:
            return None
        try:
            return obj.read().decode("utf-8")
        finally:
            obj.close()
            obj.release_conn()

    def exists(self, key: str) -> bool:
        from minio.error import S3Error

        try:
            self.client.stat_object(settings.minio_bucket, key)
            return True
        except S3Error:
            return False

    def presigned_get_url(self, key: str, expires_seconds: int | None = None) -> str:
        secs = expires_seconds if expires_seconds is not None else settings.minio_presign_seconds
        return self.signing_client.presigned_get_object(
            settings.minio_bucket,
            key,
            expires=timedelta(seconds=secs),
        )


_instance: ObjectStore | None = None
_override: ObjectStore | None = None


def set_test_store(store: ObjectStore | None) -> None:
    """Inject a custom backend for tests."""
    global _override
    _override = store


def get_object_store() -> ObjectStore:
    if _override is not None:
        return _override
    global _instance
    if _instance is None:
        if settings.minio_disabled or not settings.minio_endpoint:
            _instance = InMemoryBackend()
        else:
            try:
                _instance = MinioBackend()
            except Exception as exc:  # noqa: BLE001
                logger.warning("minio init failed (%s) — falling back to in-memory store", exc)
                _instance = InMemoryBackend()
    return _instance
