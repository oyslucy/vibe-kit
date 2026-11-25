"""User-facing error type."""


class VibeError(Exception):
    """An expected failure with a friendly message and an optional hint."""

    def __init__(self, message: str, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint
