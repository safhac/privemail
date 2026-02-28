import logging
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc 

from models.schemas import InboxItem
from database.db import get_db, Draft, Email

router = APIRouter(
    prefix="/inbox",
    tags=["Inbox"],
)

@router.get("/", response_model=List[InboxItem])
def get_inbox_list(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100)
):
    """
    Fetches all processed emails, joining any associated drafts.
    Sorted by urgency. Excludes archived and replied emails.
    """
    try:
        offset = (page - 1) * page_size
        results = (
            db.query(
                Email.id.label("email_id"),
                Email.sender.label("correspondent"),
                Email.subject,
                Email.local_priority_score,
                Draft.id.label("draft_id"),
                Draft.status.label("draft_status")
            )
            .outerjoin(Draft, Email.id == Draft.email_id)
            # --- MODIFIED: Filter out 'archived_no_reply' AND 'replied' ---
            .filter(Email.status.notin_(["archived_no_reply", "replied"]))
            # --------------------------------------------------------------
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
                    draft_status=email.draft_status,
                    local_priority_score=email.local_priority_score or 0.0
                )
            )
        return inbox_items
    except Exception as e:
        print(f"Error fetching inbox list: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch inbox list")