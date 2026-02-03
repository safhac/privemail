"""Gmail provider implementation wrapping existing google.py."""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from .base import EmailProvider, EmailMessage, SendResult
import clients.google as google_client

logging.basicConfig(level=logging.INFO)


class GmailProvider(EmailProvider):
    """Gmail implementation using existing google.py functions."""

    def __init__(self):
        """Initialize Gmail provider."""
        self._service = None

    @property
    def provider_name(self) -> str:
        return "gmail"

    def _get_service(self):
        """Get or create Gmail service."""
        if self._service is None:
            self._service = google_client.get_gmail_service()
        return self._service

    async def test_connection(self) -> bool:
        """Test Gmail connection."""
        try:
            service = self._get_service()
            return service is not None
        except Exception as e:
            logging.error(f"Gmail connection test failed: {e}")
            return False

    async def fetch_unread_messages(self, limit: int = 10) -> List[EmailMessage]:
        """Fetch unread messages from Gmail."""
        service = self._get_service()
        if not service:
            return []

        try:
            stubs = google_client.fetch_new_email_stubs(service)
            messages = []

            for message_id in stubs[:limit]:
                details = google_client.fetch_email_details(service, message_id)
                if details:
                    messages.append(EmailMessage(
                        message_id=details["message_id"],
                        sender=details["sender"],
                        subject=details["subject"],
                        body_text=details["body_text"],
                        received_at=datetime.now()  # Gmail doesn't return this easily
                    ))

            return messages
        except Exception as e:
            logging.error(f"Error fetching Gmail messages: {e}")
            return []

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        reply_to_id: Optional[str] = None
    ) -> SendResult:
        """Send email via Gmail."""
        service = self._get_service()
        if not service:
            return SendResult(success=False, error="Gmail service unavailable")

        try:
            success = google_client.send_reply(service, to, subject, body)
            return SendResult(success=success, error=None if success else "Send failed")
        except Exception as e:
            logging.error(f"Error sending Gmail: {e}")
            return SendResult(success=False, error=str(e))

    async def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        reply_to_id: Optional[str] = None
    ) -> SendResult:
        """Create draft in Gmail."""
        service = self._get_service()
        if not service:
            return SendResult(success=False, error="Gmail service unavailable")

        try:
            success = google_client.create_draft(service, to, subject, body)
            return SendResult(success=success, error=None if success else "Draft creation failed")
        except Exception as e:
            logging.error(f"Error creating Gmail draft: {e}")
            return SendResult(success=False, error=str(e))

    async def get_contacts(self) -> List[Dict[str, Any]]:
        """Fetch contacts from Google."""
        service = self._get_service()
        if not service:
            return []

        try:
            return google_client.fetch_google_contacts(service)
        except Exception as e:
            logging.error(f"Error fetching Google contacts: {e}")
            return []
