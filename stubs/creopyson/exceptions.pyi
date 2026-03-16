"""Creopyson exceptions."""


class Error(Exception):
    """Base class for other exceptions."""
    ...


class MissingKey(Error):
    """Raised when the input value is too small."""
    ...


class ErrorJsonDecode(Error):
    """Raised when creoson result cannot be decoded."""
    ...
