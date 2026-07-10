"""Object-storage abstraction.

Two backends are supported, selected by ``FIREBASE_STORAGE_BUCKET``:

* ``LocalStorageClient`` — writes bytes under a local directory (default
  ``/tmp/careeros-uploads``). Used when no Firebase bucket is configured and in
  tests/CI.
* ``FirebaseStorageClient`` — generates a signed upload URL and deletes objects
  via ``firebase-admin``. Selected only when ``FIREBASE_STORAGE_BUCKET`` is set.

``firebase-admin`` is imported lazily inside the Firebase client so that a
missing dependency or credentials never break application import.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic import BaseModel

from careeros_api.core.config import settings

_UPLOAD_URL_TTL_MINUTES = 15


class UploadTarget(BaseModel):
    """Instructions describing how a client should upload a file's bytes."""

    storage_path: str
    upload_url: str
    upload_method: str
    upload_headers: dict[str, str] = {}
    expires_at: datetime | None = None


class StorageClient:
    """Abstract interface for storing and deleting document bytes."""

    kind: str

    async def create_upload_target(
        self,
        *,
        user_id: uuid.UUID,
        document_id: uuid.UUID,
        name: str,
        mime_type: str | None,
        size_bytes: int | None,
    ) -> UploadTarget:
        raise NotImplementedError

    async def save_bytes(self, *, storage_path: str, data: bytes) -> None:
        raise NotImplementedError

    async def delete_object(self, storage_path: str) -> None:
        raise NotImplementedError


class LocalStorageClient(StorageClient):
    """Writes file bytes under a configured local directory."""

    kind = "local"

    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir

    async def create_upload_target(
        self,
        *,
        user_id: uuid.UUID,
        document_id: uuid.UUID,
        name: str,
        mime_type: str | None,
        size_bytes: int | None,
    ) -> UploadTarget:
        ext = Path(name).suffix
        storage_path = os.path.join(self.base_dir, str(user_id), f"{document_id}{ext}")
        return UploadTarget(
            storage_path=storage_path,
            upload_url=f"/api/v1/documents/{document_id}/upload",
            upload_method="POST",
            upload_headers={},
            expires_at=None,
        )

    async def save_bytes(self, *, storage_path: str, data: bytes) -> None:
        path = Path(storage_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    async def delete_object(self, storage_path: str) -> None:
        try:
            os.remove(storage_path)
        except FileNotFoundError:
            return


class FirebaseStorageClient(StorageClient):
    """Object storage backed by Firebase Storage (``firebase-admin``).

    All Firebase interaction is performed lazily so that the absence of the
    ``firebase-admin`` package or credentials never prevents application import.
    """

    kind = "firebase"

    def __init__(self, bucket_name: str) -> None:
        self.bucket_name = bucket_name

    async def create_upload_target(
        self,
        *,
        user_id: uuid.UUID,
        document_id: uuid.UUID,
        name: str,
        mime_type: str | None,
        size_bytes: int | None,
    ) -> UploadTarget:
        del size_bytes
        ext = Path(name).suffix
        object_path = f"users/{user_id}/{document_id}{ext}"
        storage_path = f"gs://{self.bucket_name}/{object_path}"
        url, headers, expires_at = self._signed_upload_url(
            object_path, mime_type or "application/octet-stream"
        )
        return UploadTarget(
            storage_path=storage_path,
            upload_url=url,
            upload_method="PUT",
            upload_headers=headers,
            expires_at=expires_at,
        )

    async def save_bytes(self, *, storage_path: str, data: bytes) -> None:
        # With Firebase the client uploads bytes directly to the signed URL; the
        # server never receives the bytes in this flow.
        raise NotImplementedError("Firebase uploads go directly to the signed URL")

    async def delete_object(self, storage_path: str) -> None:
        from firebase_admin import storage

        bucket = storage.bucket(self.bucket_name)
        object_path = storage_path.split(f"gs://{self.bucket_name}/", 1)[-1]
        blob = bucket.blob(object_path)
        blob.delete()

    def _signed_upload_url(
        self, object_path: str, content_type: str
    ) -> tuple[str, dict[str, str], datetime]:
        from firebase_admin import storage

        bucket = storage.bucket(self.bucket_name)
        blob = bucket.blob(object_path)
        expires_at = datetime.now(tz=UTC) + timedelta(minutes=_UPLOAD_URL_TTL_MINUTES)
        url: str = blob.generate_signed_url(
            version="v4",
            expiration=_UPLOAD_URL_TTL_MINUTES * 60,
            method="PUT",
            content_type=content_type,
        )
        return url, {"Content-Type": content_type}, expires_at


def get_storage_client() -> StorageClient:
    """Return the configured storage client (process-wide singleton).

    Local storage is the default; Firebase is selected only when
    ``FIREBASE_STORAGE_BUCKET`` is set.
    """
    bucket = getattr(settings, "FIREBASE_STORAGE_BUCKET", None)
    if bucket:
        return FirebaseStorageClient(bucket)
    return LocalStorageClient(getattr(settings, "UPLOAD_DIR", "/tmp/careeros-uploads"))
