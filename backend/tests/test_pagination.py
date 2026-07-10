"""Unit tests for cursor pagination helpers (no database required)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest

from careeros_api.repositories.base import decode_cursor, encode_cursor


def _ts(second: int) -> datetime:
    """A deterministic timezone-aware timestamp for ordering tests."""
    return datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC) + timedelta(seconds=second)


def test_encode_decode_round_trip_preserves_values() -> None:
    created_at = _ts(42)
    entity_id = uuid.uuid4()

    cursor = encode_cursor(created_at, entity_id)
    decoded_at, decoded_id = decode_cursor(cursor)

    assert decoded_at == created_at
    assert decoded_id == entity_id


def test_encoded_cursor_is_url_safe_and_padding_free() -> None:
    cursor = encode_cursor(_ts(0), uuid.UUID(int=0))
    # No characters that would corrupt a query string, and no '=' padding.
    assert "=" not in cursor
    for char in cursor:
        assert char.isalnum() or char in "-_"


def test_decode_rejects_garbage_cursor() -> None:
    with pytest.raises(ValueError):
        decode_cursor("not-a-valid-cursor!!")


@pytest.mark.parametrize("delta_seconds", [0, 1, 30, 3600])
def test_decode_is_exact_inverse_of_encode(delta_seconds: int) -> None:
    created_at = datetime(2026, 7, 9, 12, 0, 0, tzinfo=UTC) + timedelta(seconds=delta_seconds)
    entity_id = uuid.uuid4()

    assert (created_at, entity_id) == decode_cursor(encode_cursor(created_at, entity_id))


def test_cursors_are_monotonic_under_desc_order() -> None:
    """Under ``ORDER BY created_at DESC, id DESC`` successive rows produce
    cursors that decode to strictly decreasing ``(created_at, id)`` tuples."""
    base_ts = _ts(100)
    same_time = [(base_ts, uuid.uuid4()) for _ in range(3)]

    ordered = sorted(same_time, key=lambda pair: pair[1], reverse=True)
    decoded = [decode_cursor(encode_cursor(ts, eid)) for ts, eid in ordered]
    for earlier, later in zip(decoded, decoded[1:], strict=False):
        assert later < earlier

    greater_ts = (base_ts + timedelta(seconds=10), uuid.UUID(int=0))
    lesser_ts = (base_ts, uuid.UUID(int=0))
    earlier_cursor = decode_cursor(encode_cursor(*greater_ts))
    later_cursor = decode_cursor(encode_cursor(*lesser_ts))
    assert later_cursor < earlier_cursor
