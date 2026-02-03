"""Email provider abstraction layer."""
from .base import EmailProvider, EmailMessage, SendResult

__all__ = ["EmailProvider", "EmailMessage", "SendResult"]
