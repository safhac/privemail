# Email Provider Abstraction Design

> **Supersedes:** `2026-02-02-fastmail-integration.md` (different approach)
>
> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add multi-provider email support to Privemail, starting with Fastmail (JMAP + API keys). Users can configure multiple providers and switch between them via settings.

**Key Decisions:**
- One provider active at a time (switch via settings, not multi-account aggregation)
- Provider abstraction via abstract base class with common interface
- Credentials stored encrypted in database (not files)
- Emails/drafts tagged with source provider, filtered by active provider in UI
- Contacts shared across providers with source tracking
- Use `jmapc` library for Fastmail JMAP implementation

---

## Architecture Overview

### Provider Abstraction Layer

```
src/clients/email_provider/
├── __init__.py          # Factory: get_active_provider()
├── base.py              # EmailProvider ABC + dataclasses
├── gmail.py             # GmailProvider (wraps existing google.py)
└── fastmail.py          # FastmailProvider (uses jmapc)
```

**Abstract Interface (`base.py`):**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class EmailMessage:
    message_id: str
    sender: str
    subject: str
    body_text: str
    received_at: datetime

@dataclass
class SendResult:
    success: bool
    provider_message_id: Optional[str]
    error: Optional[str]

class EmailProvider(ABC):
    """Abstract interface for email providers."""

    @abstractmethod
    async def fetch_unread_messages(self, limit: int = 10) -> list[EmailMessage]:
        """Fetch unread messages from inbox."""

    @abstractmethod
    async def send_email(self, to: str, subject: str, body: str,
                         reply_to_id: Optional[str] = None) -> SendResult:
        """Send an email."""

    @abstractmethod
    async def create_draft(self, to: str, subject: str, body: str,
                           reply_to_id: Optional[str] = None) -> SendResult:
        """Create a draft in the provider."""

    @abstractmethod
    async def get_contacts(self) -> list[dict]:
        """Fetch contacts from provider."""

    @abstractmethod
    async def test_connection(self) -> bool:
        """Verify credentials are valid."""
```

**Factory (`__init__.py`):**

```python
def get_active_provider() -> EmailProvider:
    """Returns configured provider instance based on settings."""
    provider_name = get_setting("email_provider", "gmail")

    if provider_name == "gmail":
        creds = get_setting("gmail_credentials")
        return GmailProvider(json.loads(creds))
    elif provider_name == "fastmail":
        return FastmailProvider(
            api_key=get_setting("fastmail_api_key"),
            account_id=get_setting("fastmail_account_id")
        )
    else:
        raise ValueError(f"Unknown provider: {provider_name}")

def get_provider_by_name(name: str) -> EmailProvider:
    """Get a specific provider by name (for sending replies via original provider)."""
    # Same logic but uses explicit name instead of active setting
```

---

## Database Changes

### New Columns

**`emails` table:**
```sql
ALTER TABLE emails ADD COLUMN provider VARCHAR DEFAULT 'gmail';
CREATE INDEX ix_emails_provider ON emails(provider);
```

**`drafts` table:**
```sql
ALTER TABLE drafts ADD COLUMN provider VARCHAR DEFAULT 'gmail';
```

**`contacts` table:**
```sql
ALTER TABLE contacts ADD COLUMN source_providers JSON DEFAULT '["google"]';
```

### New Settings Keys

| Key | Type | Description |
|-----|------|-------------|
| `email_provider` | string | Active provider: `"gmail"` or `"fastmail"` |
| `gmail_credentials` | encrypted JSON | OAuth token blob (migrated from `token.json`) |
| `fastmail_api_key` | encrypted string | Fastmail app password (`fmu1-xxxxx`) |
| `fastmail_account_id` | string | JMAP account identifier (auto-discovered) |

### Migration Strategy

1. Add columns with defaults (`provider="gmail"`, `source_providers=["google"]`)
2. On first startup after upgrade:
   - Read `app_data/token.json` if exists
   - Store contents in `gmail_credentials` setting (encrypted)
   - Delete `token.json`

---

## Provider Implementations

### Gmail Provider

Wraps existing `clients/google.py` functions:

```python
class GmailProvider(EmailProvider):
    def __init__(self, credentials: dict):
        self._credentials = credentials
        self._service = None

    def _get_service(self):
        if not self._service:
            # Build service from credentials (existing logic from google.py)
            self._service = build_gmail_service(self._credentials)
        return self._service

    async def fetch_unread_messages(self, limit=10) -> list[EmailMessage]:
        service = self._get_service()
        # Call existing fetch_unread_messages() from google.py
        # Map results to EmailMessage dataclass

    async def send_email(self, to, subject, body, reply_to_id=None) -> SendResult:
        # Call existing send_reply() from google.py

    async def create_draft(self, to, subject, body, reply_to_id=None) -> SendResult:
        # Call existing create_draft() from google.py

    async def get_contacts(self) -> list[dict]:
        # Call existing get_contacts() from google.py

    async def test_connection(self) -> bool:
        try:
            self._get_service()
            return True
        except:
            return False
```

### Fastmail Provider

New implementation using `jmapc`:

```python
from jmapc import Client
from jmapc.methods import EmailQuery, EmailGet, EmailSubmissionCreate

class FastmailProvider(EmailProvider):
    JMAP_HOST = "api.fastmail.com"

    def __init__(self, api_key: str, account_id: str):
        self._client = Client.create_with_api_token(
            host=self.JMAP_HOST,
            api_token=api_key
        )
        self._account_id = account_id

    async def fetch_unread_messages(self, limit=10) -> list[EmailMessage]:
        # Use EmailQuery to find unread in Inbox
        # Use EmailGet to fetch details
        # Map to EmailMessage dataclass

    async def send_email(self, to, subject, body, reply_to_id=None) -> SendResult:
        # Create Email object
        # Create EmailSubmission to send

    async def create_draft(self, to, subject, body, reply_to_id=None) -> SendResult:
        # Create Email in Drafts mailbox with $draft keyword

    async def get_contacts(self) -> list[dict]:
        # Use JMAP ContactCard methods

    async def test_connection(self) -> bool:
        try:
            # Simple session check
            return self._client.session is not None
        except:
            return False
```

---

## API Changes

### New Endpoints

**Fastmail Setup:**
```
POST /api/setup/fastmail
Body: {"api_key": "fmu1-xxxxx"}
Response: {"success": true, "account_id": "u12345", "email": "user@fastmail.com"}

- Tests connection via JMAP session
- Auto-discovers account_id
- Stores credentials in settings table
```

**Provider Management:**
```
GET /api/settings/providers
Response: {
    "active": "gmail",
    "configured": ["gmail", "fastmail"],
    "unconfigured": []
}

POST /api/settings/provider
Body: {"provider": "fastmail"}
Response: {"success": true, "provider": "fastmail"}

- Validates credentials exist before switching
- Returns error if provider not configured
```

### Modified Endpoints

**`GET /api/inbox`** - Filter by active provider:
```python
emails = db.query(Email).filter(
    Email.status == "processed",
    Email.provider == get_setting("email_provider")
).all()
```

**`GET /api/drafts/`** - Same filtering pattern

**`GET /api/setup/status`** - Include per-provider status:
```json
{
    "gmail_connected": true,
    "fastmail_connected": true,
    "active_provider": "fastmail"
}
```

---

## Scheduler Changes

**Provider-aware fetching:**
```python
async def async_email_fetch_job():
    try:
        provider = get_active_provider()
    except ValueError:
        return  # No provider configured

    messages = await provider.fetch_unread_messages(limit=1)

    for msg in messages:
        email = Email(
            message_id=msg.message_id,
            sender=msg.sender,
            subject=msg.subject,
            body_text=msg.body_text,
            provider=get_setting("email_provider"),  # Tag source
            status="processed"
        )
        db.add(email)
        # Continue with analysis, draft generation...
```

**Reply sending uses original provider:**
```python
async def send_draft(draft_id: int, mode: str):
    draft = get_draft(draft_id)
    email = draft.email

    # Use the provider that received the original email
    provider = get_provider_by_name(email.provider)

    if mode == "send":
        result = await provider.send_email(...)
    else:
        result = await provider.create_draft(...)
```

---

## Frontend Changes

### Setup Wizard

**Step 1: Choose Provider**
```
Which email provider do you use?

[Gmail]     [Fastmail]
```

**Step 2a (Gmail):** Existing OAuth flow

**Step 2b (Fastmail):**
```
Enter your Fastmail app password:
[________________________]

How to get an app password:
1. Go to Fastmail Settings > Privacy & Security
2. Under "App passwords", click "New app password"
3. Name it "Privemail" and copy the generated key

[Test & Connect]
```

### Settings Page

**Connected Accounts section:**
```
Email Accounts
─────────────────────────────────────────────
○ Gmail (user@gmail.com)           [Active]
● Fastmail (user@fastmail.com)     [Switch]

[+ Add another account]
```

**Switch confirmation:**
> Switch to Fastmail? You'll only see Fastmail emails until you switch back.
> [Cancel] [Switch]

### Inbox Header

Small indicator showing active provider:
```
Inbox                              [Fastmail ▾]
─────────────────────────────────────────────
```

---

## Implementation Order

| Phase | Tasks | Risk Level |
|-------|-------|------------|
| 1 | Database migration (add columns, migrate token.json) | Low |
| 2 | Provider abstraction (base class, factory) | Low |
| 3 | Gmail adapter (wrap existing google.py) | Low |
| 4 | Update scheduler & routes to use factory | Medium |
| 5 | Fastmail provider (jmapc implementation) | Medium |
| 6 | Setup endpoints (Fastmail auth, switching) | Low |
| 7 | Frontend (wizard, settings UI) | Low |
| 8 | Testing (E2E with both providers) | - |

**Key principle:** Steps 1-4 are pure refactoring. Existing Gmail users see no behavior change. Steps 5+ add new capability.

---

## Dependencies

```toml
# Add to pyproject.toml
jmapc = ">=0.8.0"
```

---

## Testing Strategy

**Unit tests:**
- Provider base class contract tests
- Gmail adapter maps correctly to interface
- Fastmail provider handles JMAP responses

**Integration tests:**
- Provider switching preserves data
- Filtered queries work correctly
- Credentials stored/retrieved correctly

**Manual E2E:**
- Set up Gmail, verify existing flow works
- Set up Fastmail, verify emails fetch
- Switch providers, verify filtering
- Reply to email, verify uses correct provider

---

## Future Extensibility

This design supports adding more providers:

1. Create `src/clients/email_provider/outlook.py`
2. Implement `OutlookProvider(EmailProvider)`
3. Add setup endpoint `/api/setup/outlook`
4. Add to factory switch statement
5. Update frontend with Outlook option

No changes needed to scheduler, routes, or database schema.
