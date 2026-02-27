import os
import os.path
import base64
import sys
import socket
import webbrowser
from typing import List, Dict, Any
import logging
import re
from pathlib import Path
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.auth.exceptions import RefreshError

# FIX: Import get_data_dir
from core.path_utils import get_app_root, get_data_dir

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- PATH CONFIGURATION ---
BASE_DIR = get_app_root()
DATA_DIR = get_data_dir()

# Credentials (Read-Only) stay with the app
CREDENTIALS_FILE = BASE_DIR / 'credentials.json'

# Token (Writable) moves to AppData
TOKEN_FILE = DATA_DIR / 'token.json'

# Scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/contacts.readonly'
]

# --- HELPER FUNCTIONS ---

def _is_port_available(port: int) -> bool:
    """Check if a port is available on localhost."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('127.0.0.1', port))
        sock.close()
        return result != 0
    except Exception:
        return False

def _find_available_port(start_port: int = 8080, max_attempts: int = 5) -> int:
    """Find an available port starting from start_port. Returns the port or raises ValueError."""
    for offset in range(max_attempts):
        port = start_port + offset
        if _is_port_available(port):
            return port
    raise ValueError(f"Could not find available port in range {start_port}-{start_port + max_attempts - 1}")

def _open_browser_for_oauth(url: str) -> None:
    """
    Open browser for OAuth flow with extra handling for frozen executables.
    """
    try:
        logging.info(f"Opening browser to: {url}")
        if getattr(sys, 'frozen', False):
            # PyInstaller frozen executable - use explicit commands
            import platform
            if platform.system() == 'Windows':
                os.startfile(url)
            elif platform.system() == 'Darwin':
                os.system(f'open "{url}"')
            else:  # Linux
                os.system(f'xdg-open "{url}"')
        else:
            # Development mode - use standard webbrowser
            webbrowser.open(url)
    except Exception as e:
        logging.warning(f"Failed to open browser automatically: {e}")
        logging.info(f"Please visit this URL manually: {url}")

def get_gmail_service():
    """Authenticates and returns a Gmail API service client."""
    creds = None
    
    if TOKEN_FILE.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        except Exception as e:
            logging.warning(f"Corrupt token file found. Deleting. Error: {e}")
            try:
                os.remove(TOKEN_FILE)
            except OSError:
                pass
            creds = None
    
    if creds and not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                logging.info("Token expired. Refreshing...")
                creds.refresh(Request())
            except (RefreshError, Exception) as e:
                logging.error(f"Token refresh failed: {e}. Deleting stale token.")
                try:
                    if TOKEN_FILE.exists():
                        os.remove(TOKEN_FILE)
                except OSError:
                    pass
                creds = None
        else:
            creds = None

    if not creds:
        if not CREDENTIALS_FILE.exists():
            logging.error(
                f"CRITICAL: credentials.json not found at '{CREDENTIALS_FILE}'. "
                "Place your Google OAuth credentials file there and restart the app."
            )
            return None

        try:
            # Find an available port (with fallback from 8080)
            oauth_port = _find_available_port(start_port=8080, max_attempts=5)
            logging.info(f"Using port {oauth_port} for OAuth callback")

            # Create flow with dynamic port
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES, redirect_uri=f'http://localhost:{oauth_port}'
            )

            logging.info(f"Starting OAuth flow on port {oauth_port}. Attempting to open browser...")

            # Prepare OAuth URL
            auth_url, _ = flow.authorization_url()
            _open_browser_for_oauth(auth_url)

            # Run local server and handle callback
            creds = flow.run_local_server(
                port=oauth_port,
                open_browser=False
            )

            # Save token to Writable Directory
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
                logging.info(f"New token saved successfully to {TOKEN_FILE}")

        except ValueError as e:
            logging.error(f"OAuth port error: {e}. All fallback ports in use.")
            return None
        except Exception as e:
            logging.error(f"OAuth flow failed: {e}")
            return None

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        logging.error(f'An error occurred building Gmail service: {error}')
        return None

# ... (Rest of file: _parse_email_body, fetch_new_email_stubs, etc. UNCHANGED) ...
# Copy the helper functions from your existing file below this line.
# Or I can provide them if needed.

def _parse_email_body(payload: Dict[str, Any]) -> str:
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                body_data = part['body'].get('data')
                if body_data:
                    return base64.urlsafe_b64decode(body_data).decode('utf-8')
            elif 'parts' in part:
                body_text = _parse_email_body(part)
                if body_text: return body_text
    elif payload.get('mimeType') == 'text/plain' and 'body' in payload:
        body_data = payload['body'].get('data')
        if body_data:
            return base64.urlsafe_b64decode(body_data).decode('utf-8')
    return "" 

def _get_header(headers: List[Dict], name: str) -> str:
    for header in headers:
        if header['name'].lower() == name.lower():
            return header['value']
    return ""

def parse_email_address(sender_string: str) -> str:
    if not sender_string: return ""
    match = re.search(r'<(.+?)>', sender_string)
    if match: return match.group(1).strip()
    return sender_string.strip()

def fetch_new_email_stubs(service) -> List[str]:
    try:
        results = service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD']).execute()
        messages = results.get('messages', [])
        return [msg['id'] for msg in messages]
    except HttpError as error:
        logging.error(f'Error fetching stubs: {error}')
        return []

def fetch_email_details(service, message_id: str) -> Dict[str, Any]:
    try:
        msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
        payload = msg['payload']
        headers = payload['headers']
        return {
            "message_id": msg['id'],
            "subject": _get_header(headers, "Subject"),
            "sender": _get_header(headers, "From"),
            "body_text": _parse_email_body(payload)
        }
    except HttpError as error:
        logging.error(f'Error fetching details for {message_id}: {error}')
        return None

def get_sent_emails_for_contact(service, contact_email: str) -> List[str]:
    try:
        results = service.users().messages().list(userId='me', labelIds=['SENT'], q=f"to:{contact_email}").execute()
        messages = results.get('messages', [])
        sent_bodies = []
        for msg_stub in messages[:10]:
            details = fetch_email_details(service, msg_stub['id'])
            if details and details['body_text']:
                sent_bodies.append(details['body_text'])
        return sent_bodies
    except HttpError as error:
        logging.error(f'Error fetching sent mail: {error}')
        return []

def create_draft(service, to_email: str, subject: str, body_content: str) -> bool:
    try:
        message = MIMEText(body_content)
        message['to'] = to_email
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {'message': {'raw': raw}}
        service.users().drafts().create(userId='me', body=body).execute()
        logging.info(f"Draft created successfully for {to_email}")
        return True
    except HttpError as error:
        logging.error(f'An error occurred creating draft: {error}')
        return False

def send_reply(service, to_email: str, subject: str, body_content: str) -> bool:
    try:
        message = MIMEText(body_content)
        message['to'] = to_email
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        body = {'raw': raw}
        service.users().messages().send(userId='me', body=body).execute()
        logging.info(f"Email sent successfully to {to_email}")
        return True
    except HttpError as error:
        logging.error(f'An error occurred sending email: {error}')
        return False


def fetch_google_contacts(service) -> List[Dict[str, str]]:
    """Fetches names and emails from Google People API."""
    try:
        # We need the 'people' service, which is slightly different from 'gmail'
        # But we can use the same credentials.
        from googleapiclient.discovery import build
        people_service = build('people', 'v1', credentials=service._http.request.credentials)

        results = people_service.people().connections().list(
            resourceName='people/me',
            pageSize=1000,
            personFields='names,emailAddresses'
        ).execute()

        connections = results.get('connections', [])
        imported = []

        for person in connections:
            names = person.get('names', [])
            emails = person.get('emailAddresses', [])

            if emails:
                # Use first found name and email
                name_val = names[0].get('displayName') if names else None
                email_val = emails[0].get('value')
                
                if email_val:
                    imported.append({"name": name_val, "email": email_val})
        
        return imported
    except Exception as e:
        logging.error(f"Error fetching Google contacts: {e}")
        return []