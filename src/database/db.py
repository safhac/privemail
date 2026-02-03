import logging
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, ForeignKey, Float
from sqlalchemy.orm import sessionmaker, relationship, DeclarativeBase
from sqlalchemy.exc import OperationalError

# FIX: Import get_data_dir
from core.path_utils import get_data_dir

try:
    from core.encryption import EncryptedText
except ImportError:
    logging.warning("core.encryption.EncryptedText not found. Using simple Text.")
    EncryptedText = Text

# FIX: Define DB path in the writable User Data directory
DB_PATH = get_data_dir() / "app.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Ensure the directory exists before connecting (Safety check)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

# ... (Rest of your models: Email, Draft, Group, Contact, Setting remain unchanged) ...
# Copy the rest of your existing db.py file here starting from class Email(Base):
# or I can provide the full file if you prefer.

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
    provider = Column(String, default="gmail", index=True)
    drafts = relationship("Draft", back_populates="email")

class Draft(Base):
    __tablename__ = "drafts"
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    generated_text = Column(EncryptedText)
    final_text = Column(EncryptedText)
    status = Column(String)
    is_read_and_confirmed = Column(Boolean, default=False, nullable=False)
    provider = Column(String, default="gmail")
    email = relationship("Email", back_populates="drafts")

class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    group_goal = Column(Text, nullable=True)
    group_tone = Column(Text, nullable=True)
    group_urgency = Column(Float, nullable=True)
    color = Column(String, default="#ffffff") 
    contacts = relationship("Contact", back_populates="group")

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
    source_providers = Column(Text, default='["google"]')

class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True, index=True)
    value = Column(String)

def create_db_and_tables():
    try:
        logging.info(f"Attempting to create database tables at {DB_PATH}...")
        Base.metadata.create_all(bind=engine)
        logging.info("Database tables verified/created successfully.")
    except OperationalError as e:
        logging.error(f"FATAL: Database operation failed: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during table creation: {e}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()