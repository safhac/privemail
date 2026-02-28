import asyncio
import logging
from email.utils import parseaddr
from sqlalchemy.orm import Session

from database.db import SessionLocal, Setting
from database.db import Email, Draft, Contact
from database import db_manager

import clients.google as google_client
import clients.ai_engine as ollama_client

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# --- Database Helpers ---


def _get_setting(db: Session, key: str) -> str | None:
    setting = db.query(Setting).filter(Setting.key == key).first()
    return setting.value if setting else None


def _set_setting(db: Session, key: str, value: str):
    setting = db.query(Setting).filter(Setting.key == key).first()
    if setting:
        setting.value = value
    else:
        new_setting = Setting(key=key, value=value)
        db.add(new_setting)
    db.commit()

# --- Core Orchestration Job ---


async def async_email_fetch_job() -> bool:
    db = SessionLocal()
    try:
        # 1. CHECK PAUSE STATUS
        is_paused = _get_setting(db, "scheduler_paused")
        if is_paused == "true":
            logging.info("SCHEDULER: Paused by user. Skipping job.")
            return True

        logging.info("SCHEDULER: Running email fetch job...")

        try:
            service = google_client.get_gmail_service()
        except Exception as e:
            logging.error(f"SCHEDULER: Google Auth/Connection failed: {e}")
            return False

        if not service:
            logging.warning("SCHEDULER: Gmail service is unavailable.")
            return False

        stubs = google_client.fetch_new_email_stubs(service)
        if not stubs:
            logging.info("SCHEDULER: No new emails found.")
            return True

        logging.info(f"SCHEDULER: Found {len(stubs)} new email(s).")

        # Find the first stub that hasn't been processed yet
        message_id = None
        for stub in stubs:
            if not db.query(Email).filter(Email.message_id == stub).first():
                message_id = stub
                break

        if message_id is None:
            logging.info("SCHEDULER: All fetched emails already processed.")
            return True

        details = google_client.fetch_email_details(service, message_id)
        if not details:
            return False

        real_name, email_address = parseaddr(details['sender'])

        # Lightweight Archive for No-Reply
        if 'no-reply' in email_address.lower() or 'noreply' in email_address.lower():
            logging.info(
                f"SCHEDULER: Archiving no-reply from {email_address}.")
            email_obj = Email(
                message_id=details['message_id'],
                sender=details['sender'],
                subject="[No Reply]",
                body_text=None,
                status="archived_no_reply"
            )
            db.add(email_obj)
            db.commit()
            return True

        # Save Valid Email
        email_obj = Email(
            message_id=details['message_id'],
            sender=details['sender'],
            subject=details['subject'],
            body_text=details['body_text'],
            status="processed"
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
                auto_draft_enabled=True
            )
            db.add(contact)
            db.commit()
            db.refresh(contact)

        # AI Analysis
        logging.info(f"SCHEDULER: Analyzing email {email_id}...")
        analysis_result = await ollama_client.analyze_correspondent(details['body_text'])

        email_obj.correspondent_tone = analysis_result.get(
            'correspondent_tone')
        email_obj.correspondent_goal = analysis_result.get(
            'correspondent_goal')
        email_obj.correspondent_evidence = analysis_result.get(
            'correspondent_evidence')
        db.commit()

        await db_manager.calculate_local_priority(email_id)

        # --- DRAFT GENERATION LOGIC (UPDATED) ---

        # Check for Manual Mode
        manual_mode = _get_setting(db, "manual_mode") == "true"

        if manual_mode:
            logging.info(
                f"SCHEDULER: Manual Mode ON. Creating pending draft for {email_id}.")
            new_draft = Draft(
                email_id=email_id,
                generated_text="",  # Empty
                final_text="",
                status="pending",  # New status
                is_read_and_confirmed=False
            )
            db.add(new_draft)
            db.commit()
        else:
            logging.info(f"SCHEDULER: Generating draft for {email_id}...")
            generated_text = await ollama_client.generate_draft_reply(
                context=details['body_text'],
                contact=contact
            )

            if generated_text:
                new_draft = Draft(
                    email_id=email_id,
                    generated_text=generated_text,
                    final_text=generated_text,
                    status="draft",
                    is_read_and_confirmed=False
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

_scheduler_running = False
scheduler_task: asyncio.Task | None = None


async def run_scheduler_loop(default_interval: int):
    logging.info(
        f"SCHEDULER: Loop starting. Default Interval: {default_interval}s")
    while True:
        success = await async_email_fetch_job()

        if success:
            db = SessionLocal()
            try:
                interval_str = _get_setting(db, "scan_interval")
                wait_time = int(
                    interval_str) if interval_str else default_interval
            except:
                wait_time = default_interval
            finally:
                db.close()
        else:
            wait_time = 60
            logging.warning(
                "SCHEDULER: Job failed. Entering short backoff (60s).")

        logging.info(f"SCHEDULER: Sleeping for {wait_time} seconds...")
        await asyncio.sleep(wait_time)


def start_scheduler_if_needed():
    global _scheduler_running, scheduler_task
    if _scheduler_running:
        return
    logging.info("Starting scheduler loop...")

    db = SessionLocal()
    try:
        interval_str = _get_setting(db, "scan_interval")
        interval = int(interval_str) if interval_str else 300
    except:
        interval = 300
    finally:
        db.close()

    scheduler_task = asyncio.create_task(run_scheduler_loop(interval))
    _scheduler_running = True
