import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Any

import redis

from app.config import settings


_BINARY_PREFIX = "base64:"


def _redis_client():
    """Redis client.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Returns:
        Service result produced by the operation."""
    return redis.from_url(settings.REDIS_URL, decode_responses=False)


def _dynamodb_table():
    """Dynamodb table.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Returns:
        Service result produced by the operation.

    Raises:
        RuntimeError: When required infrastructure or configuration is unavailable."""
    if not settings.DYNAMODB_KV_TABLE:
        raise RuntimeError("DYNAMODB_KV_TABLE is required when KV_BACKEND=dynamodb")
    import boto3

    resource = boto3.resource("dynamodb", region_name=settings.AWS_REGION)
    return resource.Table(settings.DYNAMODB_KV_TABLE)


def _expires_at(ttl_seconds: int | None) -> int | None:
    """Expires at.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        ttl_seconds: Optional time-to-live in seconds before the value expires.

    Returns:
        int | None when a matching value is available; otherwise None."""
    if ttl_seconds is None:
        return None
    expires = datetime.now(timezone.utc) + timedelta(seconds=max(1, ttl_seconds))
    return int(expires.timestamp())


def _encode_value(value: str | bytes) -> str:
    """Encode value.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        value: Value to store or transform.

    Returns:
        String value produced by the operation."""
    if isinstance(value, bytes):
        return _BINARY_PREFIX + base64.b64encode(value).decode("ascii")
    return value


def _decode_value(value: str) -> str | bytes:
    """Decode value.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        value: Value to store or transform.

    Returns:
        str | bytes produced by the operation."""
    if value.startswith(_BINARY_PREFIX):
        return base64.b64decode(value[len(_BINARY_PREFIX):])
    return value


def get_text(key: str) -> str | bytes | None:
    """Get text.

    Loads the requested service state and applies the missing-resource behavior expected by API callers.

    Args:
        key: Storage key used to identify the cached value.

    Returns:
        str | bytes | None when a matching value is available; otherwise None."""
    if settings.KV_BACKEND == "dynamodb":
        try:
            response = _dynamodb_table().get_item(Key={"pk": key})
        except Exception:
            return None
        item = response.get("Item")
        if not item:
            return None
        expires = item.get("expires_at")
        if expires is not None and int(expires) <= int(datetime.now(timezone.utc).timestamp()):
            delete(key)
            return None
        value = item.get("value")
        if value is None:
            return None
        return _decode_value(value)

    value = _redis_client().get(key)
    if value is None:
        return None
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError:
        return value


def set_text(key: str, value: str | bytes, ttl_seconds: int | None = None) -> None:
    """Set text.

    Updates response or storage state while keeping cookie and cache settings centralized.

    Args:
        key: Storage key used to identify the cached value.
        value: Value to store or transform.
        ttl_seconds: Optional time-to-live in seconds before the value expires. Defaults to None.

    Returns:
        None."""
    if settings.KV_BACKEND == "dynamodb":
        item: dict[str, Any] = {
            "pk": key,
            "value": _encode_value(value),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        expires = _expires_at(ttl_seconds)
        if expires is not None:
            item["expires_at"] = expires
        _dynamodb_table().put_item(Item=item)
        return

    client = _redis_client()
    if ttl_seconds is None:
        client.set(key, value)
    else:
        client.setex(key, max(1, ttl_seconds), value)


def get_json(key: str) -> Any | None:
    """Get json.

    Loads the requested service state and applies the missing-resource behavior expected by API callers.

    Args:
        key: Storage key used to identify the cached value.

    Returns:
        Any | None when a matching value is available; otherwise None."""
    value = get_text(key)
    if value is None or isinstance(value, bytes):
        return None
    return json.loads(value)


def set_json(key: str, value: Any, ttl_seconds: int | None = None) -> None:
    """Set json.

    Updates response or storage state while keeping cookie and cache settings centralized.

    Args:
        key: Storage key used to identify the cached value.
        value: Value to store or transform.
        ttl_seconds: Optional time-to-live in seconds before the value expires. Defaults to None.

    Returns:
        None."""
    set_text(key, json.dumps(value), ttl_seconds=ttl_seconds)


def delete(key: str) -> None:
    """Delete.

    Performs the service operation behind a stable module-level interface.

    Args:
        key: Storage key used to identify the cached value.

    Returns:
        None."""
    if settings.KV_BACKEND == "dynamodb":
        _dynamodb_table().delete_item(Key={"pk": key})
        return
    _redis_client().delete(key)


def exists(key: str) -> bool:
    """Check whether.

    Evaluates service rules and returns a boolean or reason code without mutating application state.

    Args:
        key: Storage key used to identify the cached value.

    Returns:
        True when the condition is met; otherwise False."""
    if settings.KV_BACKEND == "dynamodb":
        return get_text(key) is not None
    return _redis_client().exists(key) == 1
