"""Private control-plane fingerprint helpers shared by trusted boundaries."""

from __future__ import annotations

import dataclasses
import hashlib
import hmac
import json
import secrets
from collections.abc import Mapping
from pathlib import Path
from typing import Any

_SIGNING_KEY = secrets.token_bytes(32)


def _normalise(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _normalise(value.model_dump(mode="json"))
    if dataclasses.is_dataclass(value):
        return _normalise(dataclasses.asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _normalise(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_normalise(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


def digest(value: Any) -> str:
    """Return a stable SHA-256 digest for a semantic control boundary."""

    encoded = json.dumps(_normalise(value), sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def signature(kind: str, payload: Any) -> str:
    """Sign an immutable capability payload with a process-local control-plane key."""

    encoded = json.dumps(
        {"kind": kind, "payload": _normalise(payload)},
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hmac.new(_SIGNING_KEY, encoded, hashlib.sha256).hexdigest()


def has_valid_signature(kind: str, payload: Any, value: str) -> bool:
    """Verify a signed payload without trusting its cached digest or mutable fields."""

    return hmac.compare_digest(signature(kind, payload), value)


def file_digest(path: Path) -> str:
    """Return the content digest of an expected local source dataset."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def registry_digest(registry: Any) -> str:
    """Fingerprint reviewed registry assets without exposing its SQLite cache."""

    return digest(
        {
            "concepts": registry.concepts,
            "products": registry.products,
            "mappings": registry.mappings,
            "metrics": registry.metrics,
            "rules": registry.rules,
        }
    )
