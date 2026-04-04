class FlowgerError(Exception):
    """Base exception for all Flowger application errors."""


class BankProviderError(FlowgerError):
    """Raised when communication with the bank provider fails."""


class KeyReadError(FlowgerError):
    """Raised when the RSA private key cannot be read from disk."""
