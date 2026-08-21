class ConnectorError(RuntimeError):
    """Base error raised at the external-source boundary."""


class ConnectorTransientError(ConnectorError, ConnectionError):
    """A retryable remote dependency failure."""


class ConnectorConfigurationError(ConnectorError):
    """A source cannot be used because mandatory configuration is absent."""


class UnsupportedDataTypeError(ConnectorError):
    """A connector or adapter does not support the requested data category."""


class NormalizationError(ValueError):
    """Raw source data cannot be converted into the canonical schema."""
