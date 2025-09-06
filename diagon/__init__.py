"""Diagon: Data validation, scenario management, and utilities."""

from .stopgate import StopConfig, pause_on_error, stop_until_resolved

__all__ = [
    "StopConfig",
    "pause_on_error",
    "stop_until_resolved",
    "__version__",
]

__version__ = "0.0.1"
