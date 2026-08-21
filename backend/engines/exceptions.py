class EngineError(RuntimeError):
    """Base deterministic-engine failure."""


class EngineInputError(EngineError, ValueError):
    """Input data violates an engine contract."""


class InsufficientDataError(EngineInputError):
    """A calculation does not have the minimum required observations."""
