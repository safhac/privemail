import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import logging
import asyncio

# --- NEW IMPORTS ---
from sqlalchemy.orm import Session
from .db import Email, Contact, SessionLocal
# -------------------

# Define score increments (Preserved from your code)
STRONG_INCREMENT = 50.0  # Adjusted to match my logic (was 100)
MODERATE_INCREMENT = 20.0 # Adjusted to match my logic (was 30)

# --- Encryption Logic (Unchanged) ---
class EncryptionManager:
    def __init__(self):
        self._key = None
        self._fernet = None

    def derive_key(self, master_password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        self._key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        self._fernet = Fernet(self._key)
        print("Encryption key derived and loaded.")

    def encrypt_data(self, data: str) -> str:
        if not self._fernet:
            raise ValueError("Encryption key is not initialized.")
        return self._fernet.encrypt(data.encode()).decode('utf-8')

    def decrypt_data(self, encrypted_data: str) -> str:
        if not self._fernet:
            raise ValueError("Encryption key is not initialized.")
        try:
            return self._fernet.decrypt(encrypted_data.encode()).decode('utf-8')
        except Exception as e:
            print(f"Decryption failed: {e}")
            return "DECRYPTION_FAILED"

encryption_manager = EncryptionManager()
APP_SALT = os.urandom(16)

def initialize_encryption(master_password: str):
    encryption_manager.derive_key(master_password, APP_SALT)

# --- NEW: Urgency Scoring Logic (Real Implementation) ---

async def calculate_local_priority(email_id: int):
    """
    Calculates the urgency score for an email based on AI analysis
    and Contact settings. Updates the Email record directly.
    """
    logging.info(f"DB_MANAGER: Calculating priority for Email {email_id}...")
    db = SessionLocal()
    try:
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            logging.error(f"DB_MANAGER: Email {email_id} not found.")
            return

        # 1. Parse Sender Email to find Contact
        # (Simplified regex for matching contact)
        sender_clean = email.sender
        if "<" in sender_clean:
             sender_clean = sender_clean.split("<")[1].strip(">")
             
        contact = db.query(Contact).filter(Contact.email_address == sender_clean).first()

        # 2. Base Score
        score = 10.0 # Baseline for being an email

        # 3. AI-Derived Score (The "Sentiment" factor)
        tone = (email.correspondent_tone or "").lower()
        
        # Use your STRONG_INCREMENT constant
        if "urgent" in tone or "immediate" in tone or "asap" in tone:
            score += STRONG_INCREMENT
        elif "anxious" in tone or "concerned" in tone:
            score += (STRONG_INCREMENT / 2) # Half strength for anxiety
        elif "angry" in tone or "frustrated" in tone:
            score += (STRONG_INCREMENT / 1.5)
        
        # 4. User-Defined Priority (The "Contact" factor)
        if contact:
            # If user set a high tone strength (0.0 - 1.0), we treat it as higher priority
            # Use your MODERATE_INCREMENT constant
            if contact.tone_strength:
                score += (contact.tone_strength * MODERATE_INCREMENT)
            
            # Keyword checks in Goal
            contact_goal = (contact.goal or "").lower()
            if "vip" in contact_goal or "priority" in contact_goal:
                score += (MODERATE_INCREMENT * 2)
        
        # 5. Update Record
        email.local_priority_score = score
        db.commit()
        logging.info(f"DB_MANAGER: Updated Email {email_id} with Priority Score: {score}")

    except Exception as e:
        logging.error(f"DB_MANAGER: Error calculating priority: {e}")
    finally:
        db.close()