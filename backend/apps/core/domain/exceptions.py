"""Domain-specific errors with stable semantics for API/service translation."""


class DomainError(Exception):
    """Base class for expected business-domain errors."""


class DomainValidationError(DomainError, ValueError):
    """A value violates an invariant."""


class ConfigurationError(DomainError):
    """Required runtime configuration is absent or invalid."""


class RegistryError(DomainError):
    """A named strategy/provider/agent cannot be resolved."""


class CircuitBreakerOpenError(DomainError):
    """A protected dependency is temporarily unavailable."""


class AuditImmutabilityError(DomainError):
    """An append-only audit record was targeted for mutation."""
