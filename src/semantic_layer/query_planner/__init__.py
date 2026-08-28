"""Governed semantic discovery and typed query-planning public interface."""

from .service import QueryDiscovery, build_plan, discover_question

__all__ = ["QueryDiscovery", "build_plan", "discover_question"]
