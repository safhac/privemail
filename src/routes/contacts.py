import logging
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import vobject

from database.db import get_db, Contact
from models import schemas
import clients.google as google_client

router = APIRouter(
    prefix="/contacts",
    tags=["Contacts"],
)

# --- NEW: Import Endpoints ---

@router.post("/import/google")
def import_google_contacts(db: Session = Depends(get_db)):
    """Imports contacts from the connected Google Account."""
    service = google_client.get_gmail_service()
    if not service:
        raise HTTPException(status_code=403, detail="Google not connected")
    
    # Fetch all contacts (paginated)
    contacts_data = google_client.fetch_google_contacts(service)
    count = 0
    
    try:
        for c in contacts_data:
            # Check if exists to prevent duplicates
            exists = db.query(Contact).filter(Contact.email_address == c['email']).first()
            if not exists:
                new_c = Contact(
                    email_address=c['email'], 
                    name=c['name'], 
                    auto_draft_enabled=True
                )
                db.add(new_c)
                count += 1
        
        db.commit()
        return {"status": "success", "imported_count": count}
        
    except Exception as e:
        db.rollback()
        logging.error(f"Google Import Error: {e}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@router.post("/import/vcard")
async def import_vcard(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Imports contacts from a uploaded .vcf file (Phone export)."""
    try:
        content = await file.read()
        # Decode bytes to string, ignoring errors for weird characters
        content_str = content.decode('utf-8', errors='ignore')
        
        count = 0
        # vobject parses the vCard string
        for card in vobject.readComponents(content_str):
            try:
                # Skip cards without email
                if not hasattr(card, 'email'): 
                    continue
                
                email_val = card.email.value
                fn_val = card.fn.value if hasattr(card, 'fn') else None
                
                # Check duplicate
                exists = db.query(Contact).filter(Contact.email_address == email_val).first()
                if not exists:
                    new_c = Contact(
                        email_address=email_val, 
                        name=fn_val, 
                        auto_draft_enabled=True
                    )
                    db.add(new_c)
                    count += 1
            except Exception as inner_e:
                logging.warning(f"Skipping malformed vCard entry: {inner_e}")
                continue 
                
        db.commit()
        return {"status": "success", "imported_count": count}
        
    except Exception as e:
        db.rollback()
        logging.error(f"vCard Import Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse vCard: {str(e)}")

# --- EXISTING: CRUD Endpoints ---

@router.post("/", response_model=schemas.ContactDetail)
def create_or_update_contact(
    contact: schemas.ContactCreate, 
    db: Session = Depends(get_db)
):
    """
    Create a new contact or update an existing one.
    """
    logging.info(f"Attempting to create/update contact: {contact.email_address}")

    db_contact = db.query(Contact).filter(
        Contact.email_address == contact.email_address
    ).first()
    
    if db_contact:
        logging.info(f"Contact '{contact.email_address}' found, updating details...")
        db_contact.name = contact.name
        db_contact.contact_group = contact.contact_group 
        db_contact.group_id = contact.group_id 
        db_contact.tone = contact.tone
        db_contact.tone_strength = contact.tone_strength
        db_contact.goal = contact.goal
        db_contact.auto_draft_enabled = contact.auto_draft_enabled
    else:
        logging.info(f"Contact '{contact.email_address}' not found, creating new entry...")
        db_contact = Contact(
            email_address=contact.email_address,
            name=contact.name,
            contact_group=contact.contact_group,
            group_id=contact.group_id,
            tone=contact.tone,
            tone_strength=contact.tone_strength,
            goal=contact.goal,
            auto_draft_enabled=contact.auto_draft_enabled
        )
        db.add(db_contact)

    try:
        db.commit()
        db.refresh(db_contact)
        logging.info(f"Contact '{contact.email_address}' saved successfully.")
        return db_contact
    except Exception as e:
        db.rollback()
        logging.error(f"Error saving contact {contact.email_address}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update contact.")

@router.get("/", response_model=List[schemas.ContactDetail])
def get_contacts_list(db: Session = Depends(get_db)):
    """List all contacts."""
    try:
        contacts = db.query(Contact).all()
        return contacts
    except Exception as e:
        logging.error(f"Error fetching contact list: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch contacts.")

@router.get("/{email_address}", response_model=schemas.ContactDetail)
def get_contact_detail(email_address: str, db: Session = Depends(get_db)):
    """Get a single contact by email."""
    try:
        contact = db.query(Contact).filter(Contact.email_address == email_address).first()
        if not contact:
            logging.warning(f"Contact not found: {email_address}")
            raise HTTPException(status_code=404, detail="Contact not found")
        return contact
    except HTTPException:
        raise 
    except Exception as e:
        logging.error(f"Error fetching contact {email_address}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch contact.")