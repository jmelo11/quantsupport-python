"""Internal initialization of the native error boundary."""

from typing import Any

def _initialize(QSError: type[Exception]) -> dict[str, Any]: ...
