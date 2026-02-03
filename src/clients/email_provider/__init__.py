"""Email provider abstraction layer."""
from .base import EmailProvider, EmailMessage, SendResult
from .gmail import GmailProvider
from .fastmail import FastmailProvider

__all__ = [
    "EmailProvider",
    "EmailMessage",
    "SendResult",
    "GmailProvider",
    "FastmailProvider",
]
