"""Fastmail provider implementation using JMAP."""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from jmapc import Client
from jmapc.models import (
    Email as JMAPEmail,
    EmailAddress,
    EmailBodyPart,
    EmailBodyValue,
    EmailSubmission,
    Mailbox,
)
from jmapc.methods import (
    EmailGet,
    EmailQuery,
    EmailSet,
    EmailSubmissionSet,
    MailboxQuery,
)

from .base import EmailProvider, EmailMessage, SendResult

logging.basicConfig(level=logging.INFO)


class FastmailProvider(EmailProvider):
    """Fastmail implementation using JMAP protocol."""

    JMAP_HOST = "api.fastmail.com"

    def __init__(self, api_token: str, account_id: Optional[str] = None):
        """Initialize Fastmail provider.

        Args:
            api_token: Fastmail app password (fmu1-xxxxx format)
            account_id: JMAP account ID (auto-discovered if not provided)
        """
        self._api_token = api_token
        self._account_id = account_id
        self._client: Optional[Client] = None

    @property
    def provider_name(self) -> str:
        return "fastmail"

    def _get_client(self) -> Client:
        """Get or create JMAP client."""
        if self._client is None:
            self._client = Client.create_with_api_token(
                host=self.JMAP_HOST,
                api_token=self._api_token
            )
        return self._client

    def _get_account_id(self) -> str:
        """Get account ID, discovering if necessary."""
        if self._account_id is None:
            client = self._get_client()
            # The primary account for mail
            self._account_id = client.account_id
        return self._account_id

    async def test_connection(self) -> bool:
        """Test Fastmail connection."""
        try:
            client = self._get_client()
            # Accessing account_id triggers session fetch
            account_id = self._get_account_id()
            return account_id is not None
        except Exception as e:
            logging.error(f"Fastmail connection test failed: {e}")
            return False

    async def _get_inbox_id(self) -> Optional[str]:
        """Get the Inbox mailbox ID."""
        try:
            client = self._get_client()
            account_id = self._get_account_id()

            result = client.request(
                MailboxQuery(account_id=account_id, filter={"role": "inbox"})
            )

            if result and result.ids:
                return result.ids[0]
            return None
        except Exception as e:
            logging.error(f"Error getting inbox ID: {e}")
            return None

    async def _get_drafts_id(self) -> Optional[str]:
        """Get the Drafts mailbox ID."""
        try:
            client = self._get_client()
            account_id = self._get_account_id()

            result = client.request(
                MailboxQuery(account_id=account_id, filter={"role": "drafts"})
            )

            if result and result.ids:
                return result.ids[0]
            return None
        except Exception as e:
            logging.error(f"Error getting drafts ID: {e}")
            return None

    async def fetch_unread_messages(self, limit: int = 10) -> List[EmailMessage]:
        """Fetch unread messages from Fastmail inbox."""
        try:
            client = self._get_client()
            account_id = self._get_account_id()
            inbox_id = await self._get_inbox_id()

            if not inbox_id:
                logging.error("Could not find Inbox")
                return []

            # Query unread emails in inbox
            query_result = client.request(
                EmailQuery(
                    account_id=account_id,
                    filter={
                        "inMailbox": inbox_id,
                        "notKeyword": "$seen"
                    },
                    sort=[{"property": "receivedAt", "isAscending": False}],
                    limit=limit
                )
            )

            if not query_result or not query_result.ids:
                return []

            # Fetch email details
            get_result = client.request(
                EmailGet(
                    account_id=account_id,
                    ids=query_result.ids,
                    properties=[
                        "id", "from", "subject", "receivedAt",
                        "bodyValues", "textBody"
                    ],
                    fetch_text_body_values=True
                )
            )

            messages = []
            for email in get_result.data:
                # Extract sender
                sender = ""
                if email.mail_from:
                    addr = email.mail_from[0]
                    if addr.name:
                        sender = f"{addr.name} <{addr.email}>"
                    else:
                        sender = addr.email

                # Extract body text
                body_text = ""
                if email.text_body and email.body_values:
                    part_id = email.text_body[0].part_id
                    if part_id in email.body_values:
                        body_text = email.body_values[part_id].value

                messages.append(EmailMessage(
                    message_id=email.id,
                    sender=sender,
                    subject=email.subject or "(no subject)",
                    body_text=body_text,
                    received_at=email.received_at
                ))

            return messages

        except Exception as e:
            logging.error(f"Error fetching Fastmail messages: {e}")
            return []

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        reply_to_id: Optional[str] = None
    ) -> SendResult:
        """Send email via Fastmail."""
        try:
            client = self._get_client()
            account_id = self._get_account_id()

            # Create email and submit in one request
            email_create = {
                "draft": JMAPEmail(
                    mail_from=[EmailAddress(email=self._get_sender_email())],
                    to=[EmailAddress(email=to)],
                    subject=subject,
                    body_values={"body": EmailBodyValue(value=body)},
                    text_body=[EmailBodyPart(part_id="body", type="text/plain")]
                )
            }

            # Create the email
            email_result = client.request(
                EmailSet(account_id=account_id, create=email_create)
            )

            if not email_result.created or "draft" not in email_result.created:
                return SendResult(success=False, error="Failed to create email")

            email_id = email_result.created["draft"].id

            # Submit the email
            submission_result = client.request(
                EmailSubmissionSet(
                    account_id=account_id,
                    create={
                        "send": EmailSubmission(
                            email_id=email_id,
                            identity_id=self._get_identity_id()
                        )
                    }
                )
            )

            if submission_result.created and "send" in submission_result.created:
                logging.info(f"Email sent successfully to {to}")
                return SendResult(success=True, provider_message_id=email_id)

            return SendResult(success=False, error="Submission failed")

        except Exception as e:
            logging.error(f"Error sending Fastmail email: {e}")
            return SendResult(success=False, error=str(e))

    async def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        reply_to_id: Optional[str] = None
    ) -> SendResult:
        """Create draft in Fastmail."""
        try:
            client = self._get_client()
            account_id = self._get_account_id()
            drafts_id = await self._get_drafts_id()

            if not drafts_id:
                return SendResult(success=False, error="Could not find Drafts folder")

            email_create = {
                "draft": JMAPEmail(
                    mailbox_ids={drafts_id: True},
                    keywords={"$draft": True},
                    mail_from=[EmailAddress(email=self._get_sender_email())],
                    to=[EmailAddress(email=to)],
                    subject=subject,
                    body_values={"body": EmailBodyValue(value=body)},
                    text_body=[EmailBodyPart(part_id="body", type="text/plain")]
                )
            }

            result = client.request(
                EmailSet(account_id=account_id, create=email_create)
            )

            if result.created and "draft" in result.created:
                draft_id = result.created["draft"].id
                logging.info(f"Draft created successfully for {to}")
                return SendResult(success=True, provider_message_id=draft_id)

            return SendResult(success=False, error="Draft creation failed")

        except Exception as e:
            logging.error(f"Error creating Fastmail draft: {e}")
            return SendResult(success=False, error=str(e))

    async def get_contacts(self) -> List[Dict[str, Any]]:
        """Fetch contacts from Fastmail.

        Note: JMAP contacts require separate capability. Returns empty for now.
        """
        # TODO: Implement when needed - requires urn:ietf:params:jmap:contacts
        logging.info("Fastmail contacts not yet implemented")
        return []

    def _get_sender_email(self) -> str:
        """Get sender email from session."""
        try:
            client = self._get_client()
            # The username is typically the email
            return client.session.username
        except:
            return ""

    def _get_identity_id(self) -> Optional[str]:
        """Get default identity ID for sending."""
        try:
            client = self._get_client()
            account_id = self._get_account_id()
            # Get first identity
            from jmapc.methods import IdentityGet
            result = client.request(IdentityGet(account_id=account_id))
            if result.data:
                return result.data[0].id
            return None
        except:
            return None
