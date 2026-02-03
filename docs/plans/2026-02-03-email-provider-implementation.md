# Email Provider Abstraction - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add multi-provider email support to Privemail, starting with Fastmail. Users configure providers once and switch via settings.

**Architecture:** Abstract `EmailProvider` base class with `GmailProvider` (wrapping existing code) and `FastmailProvider` (using jmapc). Factory pattern selects active provider. Database tracks email source for filtering.

**Tech Stack:** Python 3.10+, FastAPI, SQLAlchemy, jmapc (JMAP client), existing google-api-python-client

---

## Task 1: Add jmapc Dependency

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add jmapc to dependencies**

Add `jmapc` to the dependencies list in `pyproject.toml`:

```toml
dependencies = [
    "fastapi",
    "uvicorn",
    "sqlalchemy",
    "google-auth-oauthlib",
    "google-api-python-client",
    "ollama",
    "vobject",
    "requests",
    "httpx",
    "python-multipart>=0.0.21",
    "psutil>=7.2.1",
    "cryptography>=46.0.3",
    "jmapc>=0.8.0",
]
```

**Step 2: Install dependencies**

Run: `cd /home/offsetkeyz/projects/privemail-email-providers && uv sync`
Expected: Successfully installs jmapc

**Step 3: Verify installation**

Run: `cd /home/offsetkeyz/projects/privemail-email-providers && uv run python -c "import jmapc; print(jmapc.__version__)"`
Expected: Prints version number (0.8.x or higher)

**Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "feat: add jmapc dependency for Fastmail JMAP support"
```

---

## Task 2: Database Schema - Add Provider Columns

**Files:**
- Modify: `src/database/db.py`

**Step 1: Add provider column to Email model**

In `src/database/db.py`, add a `provider` column to the `Email` class (after `local_priority_score`):

```python
class Email(Base):
    __tablename__ = "emails"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, index=True)
    sender = Column(String, index=True)
    subject = Column(EncryptedText)
    body_text = Column(EncryptedText)
    status = Column(String)
    correspondent_tone = Column(Text, nullable=True)
    correspondent_goal = Column(Text, nullable=True)
    correspondent_evidence = Column(Text, nullable=True)
    local_priority_score = Column(Float, default=0.0, index=True)
    provider = Column(String, default="gmail", index=True)  # NEW
    drafts = relationship("Draft", back_populates="email")
```

**Step 2: Add provider column to Draft model**

Add `provider` column to `Draft` class (after `is_read_and_confirmed`):

```python
class Draft(Base):
    __tablename__ = "drafts"
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    generated_text = Column(EncryptedText)
    final_text = Column(EncryptedText)
    status = Column(String)
    is_read_and_confirmed = Column(Boolean, default=False, nullable=False)
    provider = Column(String, default="gmail")  # NEW
    email = relationship("Email", back_populates="drafts")
```

**Step 3: Add source_providers column to Contact model**

Add `source_providers` column to `Contact` class (after `style_sample_text`):

```python
class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    email_address = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    group = relationship("Group", back_populates="contacts")
    contact_group = Column(Text, nullable=True)
    tone = Column(Text, nullable=True)
    tone_strength = Column(Float, nullable=True)
    goal = Column(Text, nullable=True)
    auto_draft_enabled = Column(Boolean, default=True, nullable=False)
    style_sample_text = Column(EncryptedText, nullable=True)
    source_providers = Column(Text, default='["google"]')  # NEW - JSON array as string
```

**Step 4: Verify schema compiles**

Run: `cd /home/offsetkeyz/projects/privemail-email-providers/src && uv run python -c "from database.db import Base, Email, Draft, Contact; print('Schema OK')"`
Expected: "Schema OK"

**Step 5: Commit**

```bash
git add src/database/db.py
git commit -m "feat: add provider columns to Email, Draft, and Contact models"
```

---

## Task 3: Provider Base Class and Dataclasses

**Files:**
- Create: `src/clients/email_provider/__init__.py`
- Create: `src/clients/email_provider/base.py`

**Step 1: Create the email_provider directory**

Run: `mkdir -p /home/offsetkeyz/projects/privemail-email-providers/src/clients/email_provider`

**Step 2: Create base.py with abstract class and dataclasses**

Create `src/clients/email_provider/base.py`:

```python
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
```

**Step 3: Create empty __init__.py**

Create `src/clients/email_provider/__init__.py`:

```python
"""Email provider abstraction layer."""
from .base import EmailProvider, EmailMessage, SendResult

__all__ = ["EmailProvider", "EmailMessage", "SendResult"]
```

**Step 4: Verify imports work**

Run: `cd /home/offsetkeyz/projects/privemail-email-providers/src && uv run python -c "from clients.email_provider import EmailProvider, EmailMessage, SendResult; print('Imports OK')"`
Expected: "Imports OK"

**Step 5: Commit**

```bash
git add src/clients/email_provider/
git commit -m "feat: add EmailProvider abstract base class and dataclasses"
```

---

## Task 4: Gmail Provider - Wrap Existing Code

**Files:**
- Create: `src/clients/email_provider/gmail.py`
- Modify: `src/clients/email_provider/__init__.py`

**Step 1: Create GmailProvider class**

Create `src/clients/email_provider/gmail.py`:

```python
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
```

**Step 2: Update __init__.py to export GmailProvider**

Update `src/clients/email_provider/__init__.py`:

```python
"""Email provider abstraction layer."""
from .base import EmailProvider, EmailMessage, SendResult
from .gmail import GmailProvider

__all__ = ["EmailProvider", "EmailMessage", "SendResult", "GmailProvider"]
```

**Step 3: Verify GmailProvider imports**

Run: `cd /home/offsetkeyz/projects/privemail-email-providers/src && uv run python -c "from clients.email_provider import GmailProvider; print('GmailProvider OK')"`
Expected: "GmailProvider OK"

**Step 4: Commit**

```bash
git add src/clients/email_provider/
git commit -m "feat: add GmailProvider wrapping existing google.py"
```

---

## Task 5: Fastmail Provider - Core Implementation

**Files:**
- Create: `src/clients/email_provider/fastmail.py`
- Modify: `src/clients/email_provider/__init__.py`

**Step 1: Create FastmailProvider class**

Create `src/clients/email_provider/fastmail.py`:

```python
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
```

**Step 2: Update __init__.py to export FastmailProvider**

Update `src/clients/email_provider/__init__.py`:

```python
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
```

**Step 3: Verify FastmailProvider imports**

Run: `cd /home/offsetkeyz/projects/privemail-email-providers/src && uv run python -c "from clients.email_provider import FastmailProvider; print('FastmailProvider OK')"`
Expected: "FastmailProvider OK"

**Step 4: Commit**

```bash
git add src/clients/email_provider/
git commit -m "feat: add FastmailProvider using JMAP protocol"
```

---

## Task 6: Provider Factory

**Files:**
- Modify: `src/clients/email_provider/__init__.py`

**Step 1: Add factory functions**

Update `src/clients/email_provider/__init__.py` with factory functions:

```python
"""Email provider abstraction layer."""
import json
import logging
from typing import Optional

from .base import EmailProvider, EmailMessage, SendResult
from .gmail import GmailProvider
from .fastmail import FastmailProvider

__all__ = [
    "EmailProvider",
    "EmailMessage",
    "SendResult",
    "GmailProvider",
    "FastmailProvider",
    "get_active_provider",
    "get_provider_by_name",
]

logging.basicConfig(level=logging.INFO)


def _get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a setting from the database."""
    from database.db import SessionLocal, Setting
    db = SessionLocal()
    try:
        setting = db.query(Setting).filter(Setting.key == key).first()
        return setting.value if setting else default
    finally:
        db.close()


def get_active_provider() -> EmailProvider:
    """Get the currently active email provider.

    Returns:
        EmailProvider instance for the active provider

    Raises:
        ValueError: If provider is unknown or not configured
    """
    provider_name = _get_setting("email_provider", "gmail")
    return get_provider_by_name(provider_name)


def get_provider_by_name(name: str) -> EmailProvider:
    """Get a specific provider by name.

    Args:
        name: Provider identifier ('gmail' or 'fastmail')

    Returns:
        EmailProvider instance

    Raises:
        ValueError: If provider is unknown or not configured
    """
    if name == "gmail":
        return GmailProvider()

    elif name == "fastmail":
        api_token = _get_setting("fastmail_api_key")
        account_id = _get_setting("fastmail_account_id")

        if not api_token:
            raise ValueError("Fastmail API key not configured")

        return FastmailProvider(api_token=api_token, account_id=account_id)

    else:
        raise ValueError(f"Unknown email provider: {name}")
```

**Step 2: Verify factory imports**

Run: `cd /home/offsetkeyz/projects/privemail-email-providers/src && uv run python -c "from clients.email_provider import get_active_provider, get_provider_by_name; print('Factory OK')"`
Expected: "Factory OK"

**Step 3: Commit**

```bash
git add src/clients/email_provider/__init__.py
git commit -m "feat: add provider factory functions"
```

---

## Task 7: Update Scheduler to Use Provider Abstraction

**Files:**
- Modify: `src/scheduler.py`

**Step 1: Update imports**

At the top of `src/scheduler.py`, add the provider import:

```python
import asyncio
import logging
from email.utils import parseaddr
from sqlalchemy.orm import Session

from database.db import SessionLocal, Setting
from database.db import Email, Draft, Contact
from database import db_manager

from clients.email_provider import get_active_provider  # NEW
import clients.google as google_client  # Keep for parse_email_address
import clients.ai_engine as ollama_client
```

**Step 2: Update async_email_fetch_job function**

Replace the Gmail-specific code with provider abstraction:

```python
async def async_email_fetch_job() -> bool:
    db = SessionLocal()
    try:
        # 1. CHECK PAUSE STATUS
        is_paused = _get_setting(db, "scheduler_paused")
        if is_paused == "true":
            logging.info("SCHEDULER: Paused by user. Skipping job.")
            return True

        logging.info("SCHEDULER: Running email fetch job...")

        # 2. GET ACTIVE PROVIDER
        try:
            provider = get_active_provider()
            provider_name = provider.provider_name
        except ValueError as e:
            logging.warning(f"SCHEDULER: No provider configured: {e}")
            return True  # Not an error, just not set up yet
        except Exception as e:
            logging.error(f"SCHEDULER: Provider init failed: {e}")
            return False

        # 3. TEST CONNECTION
        if not await provider.test_connection():
            logging.warning(f"SCHEDULER: {provider_name} connection failed.")
            return False

        # 4. FETCH MESSAGES
        messages = await provider.fetch_unread_messages(limit=1)
        if not messages:
            logging.info("SCHEDULER: No new emails found.")
            return True

        logging.info(f"SCHEDULER: Found {len(messages)} new email(s).")

        # Process one at a time
        msg = messages[0]

        # Check DB first
        existing_email = db.query(Email).filter(
            Email.message_id == msg.message_id).first()
        if existing_email:
            return True

        real_name, email_address = parseaddr(msg.sender)

        # Lightweight Archive for No-Reply
        if 'no-reply' in email_address.lower() or 'noreply' in email_address.lower():
            logging.info(
                f"SCHEDULER: Archiving no-reply from {email_address}.")
            email_obj = Email(
                message_id=msg.message_id,
                sender=msg.sender,
                subject="[No Reply]",
                body_text=None,
                status="archived_no_reply",
                provider=provider_name  # NEW
            )
            db.add(email_obj)
            db.commit()
            return True

        # Save Valid Email
        email_obj = Email(
            message_id=msg.message_id,
            sender=msg.sender,
            subject=msg.subject,
            body_text=msg.body_text,
            status="processed",
            provider=provider_name  # NEW
        )
        db.add(email_obj)
        db.commit()
        db.refresh(email_obj)
        email_id = email_obj.id

        # Auto-Save Contact Name
        contact = db.query(Contact).filter(
            Contact.email_address == email_address).first()
        if not contact:
            logging.info(
                f"SCHEDULER: Creating new contact: {real_name or email_address}")
            contact = Contact(
                email_address=email_address,
                name=real_name if real_name else None,
                auto_draft_enabled=True,
                source_providers=f'["{provider_name}"]'  # NEW
            )
            db.add(contact)
            db.commit()
            db.refresh(contact)

        # AI Analysis
        logging.info(f"SCHEDULER: Analyzing email {email_id}...")
        analysis_result = await ollama_client.analyze_correspondent(msg.body_text)

        email_obj.correspondent_tone = analysis_result.get(
            'correspondent_tone')
        email_obj.correspondent_goal = analysis_result.get(
            'correspondent_goal')
        email_obj.correspondent_evidence = analysis_result.get(
            'correspondent_evidence')
        db.commit()

        await db_manager.calculate_local_priority(email_id)

        # --- DRAFT GENERATION LOGIC ---
        manual_mode = _get_setting(db, "manual_mode") == "true"

        if manual_mode:
            logging.info(
                f"SCHEDULER: Manual Mode ON. Creating pending draft for {email_id}.")
            new_draft = Draft(
                email_id=email_id,
                generated_text="",
                final_text="",
                status="pending",
                is_read_and_confirmed=False,
                provider=provider_name  # NEW
            )
            db.add(new_draft)
            db.commit()
        else:
            logging.info(f"SCHEDULER: Generating draft for {email_id}...")
            generated_text = await ollama_client.generate_draft_reply(
                context=msg.body_text,
                contact=contact
            )

            if generated_text:
                new_draft = Draft(
                    email_id=email_id,
                    generated_text=generated_text,
                    final_text=generated_text,
                    status="draft",
                    is_read_and_confirmed=False,
                    provider=provider_name  # NEW
                )
                db.add(new_draft)
                db.commit()
                logging.info(f"SCHEDULER: Draft {new_draft.id} saved.")

        return True

    except Exception as e:
        logging.error(f"CRITICAL SCHEDULER ERROR: {e}", exc_info=True)
        return False
    finally:
        db.close()
```

**Step 3: Verify scheduler compiles**

Run: `cd /home/offsetkeyz/projects/privemail-email-providers/src && uv run python -c "from scheduler import async_email_fetch_job; print('Scheduler OK')"`
Expected: "Scheduler OK"

**Step 4: Commit**

```bash
git add src/scheduler.py
git commit -m "refactor: update scheduler to use provider abstraction"
```

---

## Task 8: Update Inbox Route to Filter by Provider

**Files:**
- Modify: `src/routes/inbox.py`

**Step 1: Add provider filtering**

Update `src/routes/inbox.py`:

```python
import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from models.schemas import InboxItem
from database.db import get_db, Draft, Email, Setting

router = APIRouter(
    prefix="/inbox",
    tags=["Inbox"],
)


def _get_setting(db: Session, key: str) -> str | None:
    """Get a setting from database."""
    setting = db.query(Setting).filter(Setting.key == key).first()
    return setting.value if setting else None


@router.get("/", response_model=List[InboxItem])
def get_inbox_list(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Fetches all processed emails for the active provider.
    Sorted by urgency. Excludes archived and replied emails.
    """
    try:
        # Get active provider
        active_provider = _get_setting(db, "email_provider") or "gmail"

        offset = (page - 1) * page_size
        results = (
            db.query(
                Email.id.label("email_id"),
                Email.sender.label("correspondent"),
                Email.subject,
                Email.local_priority_score,
                Draft.id.label("draft_id")
            )
            .outerjoin(Draft, Email.id == Draft.email_id)
            .filter(Email.status.notin_(["archived_no_reply", "replied"]))
            .filter(Email.provider == active_provider)  # NEW: Filter by provider
            .order_by(desc(Email.local_priority_score))
            .offset(offset)
            .limit(page_size)
            .all()
        )

        inbox_items = []
        for email in results:
            inbox_items.append(
                InboxItem(
                    email_id=email.email_id,
                    correspondent=email.correspondent,
                    subject=email.subject,
                    has_draft=(email.draft_id is not None),
                    draft_id=email.draft_id,
                    local_priority_score=email.local_priority_score or 0.0
                )
            )
        return inbox_items
    except Exception as e:
        print(f"Error fetching inbox list: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch inbox list")
```

**Step 2: Verify route compiles**

Run: `cd /home/offsetkeyz/projects/privemail-email-providers/src && uv run python -c "from routes.inbox import router; print('Inbox route OK')"`
Expected: "Inbox route OK"

**Step 3: Commit**

```bash
git add src/routes/inbox.py
git commit -m "feat: filter inbox by active provider"
```

---

## Task 9: Update Drafts Route to Use Provider for Sending

**Files:**
- Modify: `src/routes/drafts.py`

**Step 1: Update imports**

At the top of `src/routes/drafts.py`, add provider imports:

```python
import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import PlainTextResponse
from typing import List
from sqlalchemy.orm import Session, joinedload

from models.schemas import (
    DraftSummary,
    DraftDetail,
    DraftEditRequest,
    DraftRewriteRequest
)
import clients.ai_engine as ollama_client
import clients.google as google_client
from clients.email_provider import get_provider_by_name  # NEW
from database.db import get_db, Draft, Email, Contact
from core.config import DEFAULT_OLLAMA_MODEL
from scheduler import _get_setting

router = APIRouter(prefix="/drafts", tags=["Drafts"])
```

**Step 2: Update send_draft function**

Replace the `send_draft` function with provider-aware version:

```python
@router.post("/{draft_id}/send")
async def send_draft(
    draft_id: int,
    mode: str = Query("draft", pattern="^(draft|send)$"),
    db: Session = Depends(get_db)
):
    draft = db.query(Draft).options(joinedload(Draft.email)
                                    ).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    if not draft.email:
        raise HTTPException(
            status_code=400, detail="Draft is not linked to an email context.")

    try:
        # Check Signature Setting
        include_sig = _get_setting(db, "include_signature")
        should_add_sig = True if include_sig is None else (
            include_sig == "true")

        signature = "\n\n---\n(Drafted by Privemail AI)" if should_add_sig else ""
        final_content = f"{draft.final_text}{signature}"

        to_email = google_client.parse_email_address(draft.email.sender)
        subject = f"Re: {draft.email.subject}"

        # Use the original email's provider for replies
        email_provider = draft.email.provider or "gmail"

        try:
            provider = get_provider_by_name(email_provider)
        except ValueError as e:
            raise HTTPException(
                status_code=503, detail=f"Provider {email_provider} not configured: {e}")

        # Test connection
        if not await provider.test_connection():
            raise HTTPException(
                status_code=503, detail=f"{email_provider} service unavailable.")

        if mode == "send":
            logging.info(f"DIRECT SENDING draft {draft_id} to {to_email} via {email_provider}...")
            result = await provider.send_email(to_email, subject, final_content)
            action_msg = "Email sent successfully."
        else:
            logging.info(f"Creating DRAFT for {draft_id} via {email_provider}...")
            result = await provider.create_draft(to_email, subject, final_content)
            action_msg = f"Draft created in {email_provider.title()}."

        if not result.success:
            raise HTTPException(
                status_code=500, detail=result.error or f"Failed to communicate with {email_provider}.")

        draft.status = "sent"
        draft.email.status = "replied"
        db.commit()

        return {"status": "success", "message": action_msg}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logging.error(f"Error sending draft {draft_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to process draft: {e}")
```

**Step 3: Verify route compiles**

Run: `cd /home/offsetkeyz/projects/privemail-email-providers/src && uv run python -c "from routes.drafts import router; print('Drafts route OK')"`
Expected: "Drafts route OK"

**Step 4: Commit**

```bash
git add src/routes/drafts.py
git commit -m "refactor: update draft sending to use provider abstraction"
```

---

## Task 10: Fastmail Setup Endpoint

**Files:**
- Modify: `src/routes/setup.py`

**Step 1: Add Fastmail setup endpoint**

Add to `src/routes/setup.py` after the existing imports:

```python
from clients.email_provider import FastmailProvider
```

Then add the new endpoint after the existing ones:

```python
class FastmailSetupRequest(BaseModel):
    api_key: str


@router.post("/fastmail")
async def setup_fastmail(request: FastmailSetupRequest):
    """Setup Fastmail with API key (app password)."""
    try:
        # Test connection
        provider = FastmailProvider(api_token=request.api_key)

        if not await provider.test_connection():
            return {"success": False, "error": "Connection failed. Check your API key."}

        # Get account info
        account_id = provider._get_account_id()
        sender_email = provider._get_sender_email()

        # Save credentials to database
        session = db.SessionLocal()
        try:
            _set_setting(session, "fastmail_api_key", request.api_key)
            _set_setting(session, "fastmail_account_id", account_id)
            # Don't switch provider automatically - let user choose
        finally:
            session.close()

        logging.info(f"SETUP: Fastmail connected for {sender_email}")
        return {
            "success": True,
            "account_id": account_id,
            "email": sender_email
        }

    except Exception as e:
        logging.error(f"Fastmail setup failed: {e}")
        return {"success": False, "error": str(e)}
```

**Step 2: Update status endpoint**

Update the `get_setup_status` function to include Fastmail status:

```python
@router.get("/status")
async def get_setup_status():
    # Check token in DATA_DIR
    token_path = DATA_DIR / "token.json"
    setup_flag = DATA_DIR / ".setup_complete"

    google_token_exists = token_path.exists()
    ollama_running = await ollama_client.check_ollama_status()

    # Check Fastmail configuration
    session = db.SessionLocal()
    try:
        fastmail_key = session.query(db.Setting).filter(
            db.Setting.key == "fastmail_api_key").first()
        fastmail_configured = fastmail_key is not None and fastmail_key.value is not None

        active_provider_setting = session.query(db.Setting).filter(
            db.Setting.key == "email_provider").first()
        active_provider = active_provider_setting.value if active_provider_setting else "gmail"
    finally:
        session.close()

    return {
        "google_connected": google_token_exists,
        "fastmail_connected": fastmail_configured,
        "active_provider": active_provider,
        "ollama_running": ollama_running,
        "setup_complete": setup_flag.exists()
    }
```

**Step 3: Verify route compiles**

Run: `cd /home/offsetkeyz/projects/privemail-email-providers/src && uv run python -c "from routes.setup import router; print('Setup route OK')"`
Expected: "Setup route OK"

**Step 4: Commit**

```bash
git add src/routes/setup.py
git commit -m "feat: add Fastmail setup endpoint"
```

---

## Task 11: Provider Switching Endpoint

**Files:**
- Modify: `src/routes/system.py`

**Step 1: Read current system.py**

First, check what's in system.py to understand its structure.

**Step 2: Add provider management endpoints**

Add these endpoints to `src/routes/system.py`:

```python
# Add to imports at top
from clients.email_provider import get_provider_by_name

# Add these endpoints

@router.get("/providers")
async def get_providers(db: Session = Depends(get_db)):
    """Get configured email providers."""
    # Check Gmail
    from core.path_utils import get_data_dir
    token_path = get_data_dir() / "token.json"
    gmail_configured = token_path.exists()

    # Check Fastmail
    fastmail_key = db.query(Setting).filter(Setting.key == "fastmail_api_key").first()
    fastmail_configured = fastmail_key is not None and fastmail_key.value is not None

    # Get active
    active_setting = db.query(Setting).filter(Setting.key == "email_provider").first()
    active = active_setting.value if active_setting else "gmail"

    configured = []
    if gmail_configured:
        configured.append("gmail")
    if fastmail_configured:
        configured.append("fastmail")

    return {
        "active": active,
        "configured": configured,
        "available": ["gmail", "fastmail"]
    }


@router.post("/provider")
async def switch_provider(request: dict, db: Session = Depends(get_db)):
    """Switch active email provider."""
    provider_name = request.get("provider")

    if provider_name not in ["gmail", "fastmail"]:
        raise HTTPException(status_code=400, detail="Invalid provider")

    # Verify provider is configured
    try:
        provider = get_provider_by_name(provider_name)
        if not await provider.test_connection():
            raise HTTPException(
                status_code=400,
                detail=f"{provider_name} is not properly configured"
            )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Update setting
    setting = db.query(Setting).filter(Setting.key == "email_provider").first()
    if setting:
        setting.value = provider_name
    else:
        db.add(Setting(key="email_provider", value=provider_name))
    db.commit()

    return {"success": True, "provider": provider_name}
```

**Step 3: Verify route compiles**

Run: `cd /home/offsetkeyz/projects/privemail-email-providers/src && uv run python -c "from routes.system import router; print('System route OK')"`
Expected: "System route OK"

**Step 4: Commit**

```bash
git add src/routes/system.py
git commit -m "feat: add provider listing and switching endpoints"
```

---

## Task 12: Update Drafts List to Filter by Provider

**Files:**
- Modify: `src/routes/drafts.py`

**Step 1: Update get_drafts_list function**

Update the `get_drafts_list` function in `src/routes/drafts.py`:

```python
@router.get("/", response_model=List[DraftSummary])
async def get_drafts_list(db: Session = Depends(get_db)):
    try:
        # Get active provider
        active_provider = _get_setting(db, "email_provider") or "gmail"

        drafts = db.query(Draft).options(joinedload(Draft.email)).filter(
            Draft.provider == active_provider  # NEW: Filter by provider
        ).all()

        summaries = []
        for draft in drafts:
            summaries.append(DraftSummary(
                draft_id=draft.id,
                subject=draft.email.subject if draft.email else "[No Subject]",
                status=draft.status
            ))
        return summaries
    except Exception as e:
        logging.error(f"Error fetching drafts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
```

**Step 2: Commit**

```bash
git add src/routes/drafts.py
git commit -m "feat: filter drafts list by active provider"
```

---

## Task 13: Frontend - Setup Wizard Provider Choice

**Files:**
- Modify: `src/frontend/index.html`

**Step 1: Add provider selection step**

This task involves adding a provider selection step to the existing setup wizard. The exact implementation depends on the current wizard structure.

Add provider selection HTML after the existing steps:

```html
<!-- Add this as the first step in the wizard -->
<div id="step-provider" class="setup-step">
    <h2>Choose Your Email Provider</h2>
    <p>Which email service do you use?</p>
    <div class="provider-buttons">
        <button class="provider-btn" data-provider="gmail" onclick="selectProvider('gmail')">
            <span class="provider-icon">📧</span>
            <span class="provider-name">Gmail</span>
        </button>
        <button class="provider-btn" data-provider="fastmail" onclick="selectProvider('fastmail')">
            <span class="provider-icon">✉️</span>
            <span class="provider-name">Fastmail</span>
        </button>
    </div>
</div>

<!-- Fastmail API key step -->
<div id="step-fastmail" class="setup-step" style="display: none;">
    <h2>Connect Fastmail</h2>
    <p>Enter your Fastmail app password:</p>
    <input type="password" id="fastmail-api-key" placeholder="fmu1-xxxxxxxx" />
    <div class="help-text">
        <p><strong>How to get an app password:</strong></p>
        <ol>
            <li>Go to Fastmail Settings → Privacy & Security</li>
            <li>Under "App passwords", click "New app password"</li>
            <li>Name it "Privemail" and copy the generated key</li>
        </ol>
    </div>
    <button onclick="connectFastmail()">Test & Connect</button>
    <div id="fastmail-status"></div>
</div>
```

**Step 2: Add JavaScript handlers**

Add to the JavaScript section:

```javascript
let selectedProvider = 'gmail';

function selectProvider(provider) {
    selectedProvider = provider;
    document.querySelectorAll('.provider-btn').forEach(btn => {
        btn.classList.toggle('selected', btn.dataset.provider === provider);
    });

    if (provider === 'gmail') {
        document.getElementById('step-provider').style.display = 'none';
        document.getElementById('step-google-auth').style.display = 'block';
    } else if (provider === 'fastmail') {
        document.getElementById('step-provider').style.display = 'none';
        document.getElementById('step-fastmail').style.display = 'block';
    }
}

async function connectFastmail() {
    const apiKey = document.getElementById('fastmail-api-key').value;
    const statusEl = document.getElementById('fastmail-status');

    if (!apiKey) {
        statusEl.textContent = 'Please enter your API key';
        return;
    }

    statusEl.textContent = 'Connecting...';

    try {
        const response = await fetch('/api/setup/fastmail', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ api_key: apiKey })
        });

        const data = await response.json();

        if (data.success) {
            statusEl.innerHTML = `✅ Connected as ${data.email}`;
            // Proceed to next step
            setTimeout(() => {
                document.getElementById('step-fastmail').style.display = 'none';
                document.getElementById('step-model').style.display = 'block';
            }, 1500);
        } else {
            statusEl.textContent = `❌ ${data.error}`;
        }
    } catch (error) {
        statusEl.textContent = `❌ Connection failed: ${error.message}`;
    }
}
```

**Step 3: Add CSS**

```css
.provider-buttons {
    display: flex;
    gap: 20px;
    justify-content: center;
    margin: 30px 0;
}

.provider-btn {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 30px 50px;
    border: 2px solid #ddd;
    border-radius: 12px;
    background: white;
    cursor: pointer;
    transition: all 0.2s;
}

.provider-btn:hover {
    border-color: #007bff;
    background: #f8f9fa;
}

.provider-btn.selected {
    border-color: #007bff;
    background: #e7f1ff;
}

.provider-icon {
    font-size: 48px;
    margin-bottom: 10px;
}

.provider-name {
    font-size: 18px;
    font-weight: 500;
}

.help-text {
    background: #f8f9fa;
    padding: 15px;
    border-radius: 8px;
    margin: 15px 0;
    text-align: left;
}

.help-text ol {
    margin: 10px 0;
    padding-left: 20px;
}
```

**Step 4: Commit**

```bash
git add src/frontend/index.html
git commit -m "feat: add provider selection to setup wizard"
```

---

## Task 14: Frontend - Settings Provider Switcher

**Files:**
- Modify: `src/frontend/app.html` (or relevant settings component)

**Step 1: Add provider switcher to settings**

Add a Connected Accounts section to the settings page:

```html
<div class="settings-section">
    <h3>Email Accounts</h3>
    <div id="provider-list"></div>
    <button class="btn-secondary" onclick="addProvider()">+ Add another account</button>
</div>
```

**Step 2: Add JavaScript**

```javascript
async function loadProviders() {
    const response = await fetch('/api/settings/providers');
    const data = await response.json();

    const listEl = document.getElementById('provider-list');
    listEl.innerHTML = '';

    data.configured.forEach(provider => {
        const isActive = provider === data.active;
        const div = document.createElement('div');
        div.className = 'provider-item';
        div.innerHTML = `
            <span class="provider-radio">${isActive ? '●' : '○'}</span>
            <span class="provider-label">${provider.charAt(0).toUpperCase() + provider.slice(1)}</span>
            <button class="btn-small" onclick="switchProvider('${provider}')" ${isActive ? 'disabled' : ''}>
                ${isActive ? 'Active' : 'Switch'}
            </button>
        `;
        listEl.appendChild(div);
    });
}

async function switchProvider(provider) {
    if (!confirm(`Switch to ${provider}? You'll only see ${provider} emails until you switch back.`)) {
        return;
    }

    const response = await fetch('/api/settings/provider', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider })
    });

    const data = await response.json();
    if (data.success) {
        loadProviders();
        loadInbox(); // Refresh inbox with new provider
    } else {
        alert('Failed to switch: ' + (data.detail || 'Unknown error'));
    }
}

// Load on page init
loadProviders();
```

**Step 3: Commit**

```bash
git add src/frontend/app.html
git commit -m "feat: add provider switcher to settings page"
```

---

## Task 15: Integration Test

**Files:**
- Create: `tests/test_provider_integration.py`

**Step 1: Create integration test**

```python
"""Integration tests for email provider abstraction."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

# Test provider factory
def test_get_provider_gmail_default():
    """Default provider should be Gmail."""
    with patch('clients.email_provider._get_setting', return_value='gmail'):
        from clients.email_provider import get_active_provider, GmailProvider
        provider = get_active_provider()
        assert isinstance(provider, GmailProvider)
        assert provider.provider_name == "gmail"


def test_get_provider_fastmail():
    """Should return FastmailProvider when configured."""
    def mock_setting(key, default=None):
        settings = {
            'email_provider': 'fastmail',
            'fastmail_api_key': 'fmu1-test-key',
            'fastmail_account_id': 'u12345'
        }
        return settings.get(key, default)

    with patch('clients.email_provider._get_setting', side_effect=mock_setting):
        from clients.email_provider import get_active_provider, FastmailProvider
        provider = get_active_provider()
        assert isinstance(provider, FastmailProvider)
        assert provider.provider_name == "fastmail"


def test_get_provider_fastmail_not_configured():
    """Should raise ValueError if Fastmail not configured."""
    def mock_setting(key, default=None):
        if key == 'email_provider':
            return 'fastmail'
        return None

    with patch('clients.email_provider._get_setting', side_effect=mock_setting):
        from clients.email_provider import get_active_provider
        with pytest.raises(ValueError, match="not configured"):
            get_active_provider()


# Test GmailProvider interface
@pytest.mark.asyncio
async def test_gmail_provider_interface():
    """GmailProvider should implement EmailProvider interface."""
    from clients.email_provider import GmailProvider, EmailProvider

    provider = GmailProvider()
    assert isinstance(provider, EmailProvider)
    assert provider.provider_name == "gmail"


# Test FastmailProvider interface
@pytest.mark.asyncio
async def test_fastmail_provider_interface():
    """FastmailProvider should implement EmailProvider interface."""
    from clients.email_provider import FastmailProvider, EmailProvider

    provider = FastmailProvider(api_token="test", account_id="u123")
    assert isinstance(provider, EmailProvider)
    assert provider.provider_name == "fastmail"
```

**Step 2: Run tests**

Run: `cd /home/offsetkeyz/projects/privemail-email-providers && uv run python -m pytest tests/test_provider_integration.py -v`
Expected: All tests pass

**Step 3: Commit**

```bash
git add tests/test_provider_integration.py
git commit -m "test: add provider integration tests"
```

---

## Verification Checkpoints

**After Task 6:** Test provider factory
```bash
cd /home/offsetkeyz/projects/privemail-email-providers/src
uv run python -c "
from clients.email_provider import GmailProvider, FastmailProvider
g = GmailProvider()
print(f'Gmail provider: {g.provider_name}')
f = FastmailProvider('test', 'test')
print(f'Fastmail provider: {f.provider_name}')
"
```

**After Task 11:** Test API endpoints
```bash
cd /home/offsetkeyz/projects/privemail-email-providers/src
uv run uvicorn main:app --reload &
sleep 3
curl http://localhost:8000/api/settings/providers
curl http://localhost:8000/api/setup/status
```

**After Task 15:** Full test suite
```bash
cd /home/offsetkeyz/projects/privemail-email-providers
uv run python -m pytest tests/ -v
```

---

## Final Steps

After all tasks complete:

1. **Push to fork:**
   ```bash
   git push -u origin feature/email-providers
   ```

2. **Create PR** (optional):
   ```bash
   gh pr create --title "feat: multi-provider email support (Gmail + Fastmail)" --body "..."
   ```
