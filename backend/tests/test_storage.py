"""Unit tests for the local storage client (no database required)."""

from __future__ import annotations

import uuid

import pytest

from careeros_api.core.storage import LocalStorageClient


async def test_local_storage_round_trip(tmp_path_factory: pytest.TempPathFactory) -> None:
    base = tmp_path_factory.mktemp("uploads")
    client = LocalStorageClient(str(base))
    user_id = uuid.uuid4()
    document_id = uuid.uuid4()

    target = await client.create_upload_target(
        user_id=user_id,
        document_id=document_id,
        name="resume.pdf",
        mime_type="application/pdf",
        size_bytes=4,
    )
    assert target.storage_path.endswith(".pdf")
    assert str(user_id) in target.storage_path
    assert str(document_id) in target.storage_path
    assert target.upload_method == "POST"
    assert target.upload_url == f"/api/v1/documents/{document_id}/upload"

    await client.save_bytes(storage_path=target.storage_path, data=b"abc")
    assert target.storage_path  # file now exists on disk

    fetched = await client.create_upload_target(
        user_id=user_id, document_id=document_id, name="cv.txt", mime_type=None, size_bytes=None
    )
    assert fetched.storage_path.endswith(".txt")

    await client.delete_object(target.storage_path)
    await client.delete_object(target.storage_path)  # idempotent on missing file


async def test_local_storage_creates_nested_dirs(
    tmp_path_factory: pytest.TempPathFactory,
) -> None:
    base = tmp_path_factory.mktemp("nested")
    client = LocalStorageClient(str(base))
    storage_path = f"{base}/sub/deep/file.bin"
    await client.save_bytes(storage_path=storage_path, data=b"x")
    await client.delete_object(storage_path)
