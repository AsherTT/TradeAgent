"""Typed market-data failures used to decide whether fallback is safe."""

from enum import StrEnum


class OperationalFailureReason(StrEnum):
    MISSING_CREDENTIAL = "missing_credential"
    RATE_LIMITED = "rate_limited"
    QUOTA_EXHAUSTED = "quota_exhausted"
    NETWORK = "network"
    UPSTREAM_UNAVAILABLE = "upstream_unavailable"
    FREE_ENTITLEMENT_UNAVAILABLE = "free_entitlement_unavailable"


class MarketDataOperationalError(RuntimeError):
    """A provider could not operate, but another provider may be attempted."""

    def __init__(self, message: str, *, reason: OperationalFailureReason) -> None:
        super().__init__(message)
        self.reason = reason


class MarketDataIntegrityError(RuntimeError):
    """Provider output is ambiguous or invalid and must fail closed."""
