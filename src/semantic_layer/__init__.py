"""Governed, locally runnable semantic layer for GlobalSure Insurance Group."""

__version__ = "0.1.0"

# Capability issuance and signing remain internal control-plane operations;
# callers use the governed subpackage services rather than signer primitives.
__all__ = ("__version__",)
