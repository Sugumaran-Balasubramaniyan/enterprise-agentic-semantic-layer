"""Private control-plane fingerprint helpers shared by trusted boundaries."""

from __future__ import annotations

import dataclasses
import hashlib
import hmac
import json
import os
import secrets
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any

__all__ = ("digest", "file_digest", "registry_digest")

_SIGNING_KEY_ENV = "SEMANTIC_LAYER_SIGNING_KEY"
_SIGNING_KEY_FILE_ENV = "SEMANTIC_LAYER_SIGNING_KEY_FILE"


class _SigningAuthority:
    """Internal HMAC authority; production deployments must use an external KMS/service."""

    __slots__ = ("_key",)

    def __init__(self, key: bytes) -> None:
        if len(key) != 32:
            raise ValueError("semantic-layer signing key must contain exactly 32 bytes")
        self._key = key

    def sign(self, encoded: bytes) -> str:
        return hmac.new(self._key, encoded, hashlib.sha256).hexdigest()

    def verify(self, encoded: bytes, value: str) -> bool:
        return hmac.compare_digest(self.sign(encoded), value)


def _parse_key(value: bytes, *, source: str, allow_raw: bool = False) -> bytes:
    if allow_raw and len(value) == 32:
        return value
    candidate = value.strip()
    if len(candidate) == 64:
        try:
            return bytes.fromhex(candidate.decode("ascii"))
        except (UnicodeDecodeError, ValueError) as error:
            raise ValueError(f"{source} must be 64 hexadecimal characters or 32 raw bytes") from error
    if len(candidate) == 32:
        return candidate
    raise ValueError(f"{source} must be 64 hexadecimal characters or 32 raw bytes")


def _configured_signing_key() -> bytes:
    key_value = os.environ.get(_SIGNING_KEY_ENV)
    key_file = os.environ.get(_SIGNING_KEY_FILE_ENV)
    if key_value and key_file:
        raise ValueError(f"configure only one of {_SIGNING_KEY_ENV} and {_SIGNING_KEY_FILE_ENV}")
    if key_value:
        return _parse_key(key_value.encode("ascii"), source=_SIGNING_KEY_ENV)
    if key_file:
        try:
            return _parse_key(Path(key_file).read_bytes(), source=_SIGNING_KEY_FILE_ENV, allow_raw=True)
        except OSError as error:
            raise ValueError(f"cannot read {_SIGNING_KEY_FILE_ENV}: {key_file}") from error
    # A process-local key is safe only for ephemeral/demo use; durable evidence
    # must configure a key above (or delegate signing to an external authority).
    return secrets.token_bytes(32)


@lru_cache(maxsize=1)
def _signing_authority() -> _SigningAuthority:
    return _SigningAuthority(_configured_signing_key())


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


def _sign(kind: str, payload: Any) -> str:
    """Sign an immutable capability payload through the protected authority."""

    encoded = json.dumps(
        {"kind": kind, "payload": _normalise(payload)},
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return _signing_authority().sign(encoded)


def _verify(kind: str, payload: Any, value: str) -> bool:
    """Verify a signed payload without trusting its cached digest or mutable fields."""

    encoded = json.dumps(
        {"kind": kind, "payload": _normalise(payload)},
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return _signing_authority().verify(encoded, value)


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
