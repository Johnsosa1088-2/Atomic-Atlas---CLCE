class AtlasError(Exception):
    """Base error for neutral core contract violations."""


class ValidationError(AtlasError):
    """Raised when declared data violates a neutral-core invariant."""


class RestartBlockedError(AtlasError):
    """Raised when lineage mismatch blocks silent continuation or overwrite."""
