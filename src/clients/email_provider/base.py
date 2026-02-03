"""Abstract base class for email providers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class EmailMessage:
    """Standardized email message from any provider."""
    message_id: str
    sender: str
    subject: str
    body_text: str
    received_at: Optional[datetime] = None


@dataclass
class SendResult:
    """Result of a send or create_draft operation."""
    success: bool
    provider_message_id: Optional[str] = None
    error: Optional[str] = None


class EmailProvider(ABC):
    """Abstract interface for email providers.

    All email providers (Gmail, Fastmail, etc.) must implement this interface.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier (e.g., 'gmail', 'fastmail')."""
        pass

    @abstractmethod
    async def fetch_unread_messages(self, limit: int = 10) -> List[EmailMessage]:
        """Fetch unread messages from inbox.

        Args:
            limit: Maximum number of messages to fetch

        Returns:
            List of EmailMessage objects
        """
        pass

    @abstractmethod
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        reply_to_id: Optional[str] = None
    ) -> SendResult:
        """Send an email.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            reply_to_id: Optional message ID this is replying to

        Returns:
            SendResult indicating success/failure
        """
        pass

    @abstractmethod
    async def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        reply_to_id: Optional[str] = None
    ) -> SendResult:
        """Create a draft in the provider.

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            reply_to_id: Optional message ID this is replying to

        Returns:
            SendResult indicating success/failure
        """
        pass

    @abstractmethod
    async def get_contacts(self) -> List[Dict[str, Any]]:
        """Fetch contacts from provider.

        Returns:
            List of contact dicts with 'name' and 'email' keys
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Verify credentials are valid.

        Returns:
            True if connection successful, False otherwise
        """
        pass
