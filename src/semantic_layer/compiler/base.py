"""Compiler output contracts that separate trusted SQL from logical plans."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CompiledQuery:
    """A parameterized query created solely by a trusted platform compiler."""

    sql: str
    parameters: tuple[Any, ...]
    approved_products: tuple[str, ...]
    target_platform: str = "DuckDB"
