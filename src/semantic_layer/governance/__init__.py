"""Authorization controls for semantic discovery and query plans."""

from semantic_layer.governance.policy import (
    AuthorizationDecision,
    DiscoveryAuthorizationDecision,
    authorize,
    authorize_discovery,
)

__all__ = ["AuthorizationDecision", "DiscoveryAuthorizationDecision", "authorize", "authorize_discovery"]
