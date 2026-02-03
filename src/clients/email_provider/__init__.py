"""Email provider abstraction layer."""
from .base import EmailProvider, EmailMessage, SendResult
from .gmail import GmailProvider

__all__ = ["EmailProvider", "EmailMessage", "SendResult", "GmailProvider"]
