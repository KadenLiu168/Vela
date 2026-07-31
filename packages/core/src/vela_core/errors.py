class VelaError(ValueError):
    """Base class for expected domain failures."""


class MissingMarketDataError(VelaError):
    """Raised when a caller-facing operation has no local market prices."""


class InvalidDateRangeError(VelaError):
    """Raised when a caller supplies an invalid date range."""


class BacktestDataError(VelaError):
    """Raised when required backtest market data is unavailable."""
