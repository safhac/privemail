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
from database.db import get_db, Draft, Email, Contact
from core.config import DEFAULT_OLLAMA_MODEL
from scheduler import _get_setting

router = APIRouter(prefix="/drafts", tags=["Drafts"])


@router.get("/", response_model=List[DraftSummary])
async def get_drafts_list(db: Session = Depends(get_db)):
    try:
        drafts = db.query(Draft).options(joinedload(Draft.email)).all()
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


@router.get("/{draft_id}", response_model=DraftDetail)
def get_draft_detail(draft_id: int, db: Session = Depends(get_db)):
    try:
        draft = db.query(Draft).options(
            joinedload(Draft.email)
        ).filter(Draft.id == draft_id).first()

        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")

        if not draft.email:
            raise HTTPException(
                status_code=404, detail="Draft has no associated email")

        # Prefer final_text (edits) over generated_text
        current_text = draft.final_text if draft.final_text else draft.generated_text

        data_dict = {
            "draft_id": draft.id,
            "status": draft.status,
            "generated_text": current_text,
            "original_subject": draft.email.subject,
            "original_sender": draft.email.sender,
            "original_body": draft.email.body_text,
            "is_read_and_confirmed": draft.is_read_and_confirmed,
            "correspondent_tone": draft.email.correspondent_tone,
            "correspondent_goal": draft.email.correspondent_goal,
            "correspondent_evidence": draft.email.correspondent_evidence
        }

        return DraftDetail.model_validate(data_dict)

    except Exception as e:
        logging.error(f"Error fetching draft {draft_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch draft: {e}")


@router.put("/{draft_id}")
async def update_draft(
    draft_id: int,
    request: DraftEditRequest,
    db: Session = Depends(get_db)
):
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    try:
        draft.final_text = request.final_text
        db.commit()
        return {"status": "success", "message": f"Draft {draft_id} updated."}
    except Exception as e:
        db.rollback()
        logging.error(f"Error updating draft {draft_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to save draft: {e}")


@router.post("/{draft_id}/confirm")
async def confirm_draft(draft_id: int, db: Session = Depends(get_db)):
    draft = db.query(Draft).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    try:
        draft.is_read_and_confirmed = True
        db.commit()
        return {"status": "success", "message": f"Draft {draft_id} confirmed."}
    except Exception as e:
        db.rollback()
        logging.error(f"Error confirming draft {draft_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to confirm draft: {e}")


@router.post("/{draft_id}/send")
async def send_draft(
    draft_id: int,
    mode: str = Query("draft", regex="^(draft|send)$"),
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

        service = google_client.get_gmail_service()
        if not service:
            raise HTTPException(
                status_code=503, detail="Gmail service unavailable.")

        if mode == "send":
            logging.info(f"DIRECT SENDING draft {draft_id} to {to_email}...")
            success = google_client.send_reply(
                service, to_email, subject, final_content)
            action_msg = "Email sent successfully."
        else:
            logging.info(f"Creating GMAIL DRAFT for {draft_id}...")
            success = google_client.create_draft(
                service, to_email, subject, final_content)
            action_msg = "Draft created in Gmail."

        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to communicate with Gmail API.")

        draft.status = "sent"
        draft.email.status = "replied"
        db.commit()

        return {"status": "success", "message": action_msg}

    except Exception as e:
        db.rollback()
        logging.error(f"Error sending draft {draft_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to process draft: {e}")


@router.post("/{draft_id}/generate")
async def generate_draft_manually(draft_id: int, db: Session = Depends(get_db)):
    """Manually triggers AI generation for a pending draft."""
    draft = db.query(Draft).options(joinedload(Draft.email)
                                    ).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    sender_email_str = google_client.parse_email_address(draft.email.sender)
    contact = db.query(Contact).filter(
        Contact.email_address == sender_email_str).first()

    # Fetch contact or create temporary one for context
    contact_obj = contact if contact else Contact(
        email_address=sender_email_str, auto_draft_enabled=True)

    try:
        text = await ollama_client.generate_draft_reply(
            context=draft.email.body_text,
            contact=contact_obj
        )

        if not text:
            raise HTTPException(
                status_code=500, detail="AI returned empty text.")

        draft.generated_text = text
        draft.final_text = text
        draft.status = "draft"
        db.commit()

        return {"status": "success", "text": text}
    except Exception as e:
        logging.error(f"Manual Generation Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{draft_id}/rewrite", response_class=PlainTextResponse)
async def rewrite_draft_paragraph(
    draft_id: int,
    request: DraftRewriteRequest,
    db: Session = Depends(get_db)
):
    # 1. Fetch Draft AND the original Email
    draft = db.query(Draft).options(joinedload(Draft.email)
                                    ).filter(Draft.id == draft_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")

    # 2. Get the Context
    original_context = draft.email.body_text if (
        draft.email and draft.email.body_text) else "No context available."

    # 3. Construct a Context-Aware Prompt
    system_prompt = f"""
    You are a professional email writing assistant.
    
    --- CONTEXT (The email we are replying to) ---
    {original_context[:2000]} 
    (Context truncated if too long)
    ---------------------------------------------

    --- YOUR TASK ---
    Refine the User's Draft below based on these controls:
    1. Goal: {request.goal}
    2. Tone: {request.tone}
    3. Tone Strength: {request.tone_dial_value} (0.0=subtle, 1.0=strong)
    4. Specific Instructions: {request.ad_hoc_instruction}
    
    Maintain the user's intent but improve the phrasing according to the rules above.
    Respond *only* with the refined draft text.
    """

    model_to_use = request.model or DEFAULT_OLLAMA_MODEL

    try:
        rewritten_text = await ollama_client.rewrite_paragraph_for_tone(
            system_prompt=system_prompt,
            paragraph=request.paragraph,
            model=model_to_use
        )

        draft.final_text = rewritten_text.strip()
        db.commit()

        return draft.final_text
    except Exception as e:
        logging.error(f"Error rewriting draft {draft_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
