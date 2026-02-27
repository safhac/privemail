import os
import sys
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# App Imports
from routes import contacts as contacts_router
from routes import drafts as drafts_router
from routes import inbox as inbox_router
from routes import system as system_router
from routes import groups as groups_router
from routes import setup as setup_router

import service_manager
from database import db, db_manager
import scheduler
from core.config import SETUP_COMPLETE_FLAG_PATH
# FIX: Import get_data_dir
from core.path_utils import get_app_root, get_data_dir 

# --- PATH CONFIGURATION ---
if getattr(sys, 'frozen', False):
    # Running as compiled executable (Windows)
    FRONTEND_DIR = Path(sys._MEIPASS) / "frontend"
else:
    # Running as python script (Dev)
    FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"

# --- CREDENTIAL LOADING LOGIC ---
# FIX: Use get_data_dir() for user writable data
DATA_DIR = get_data_dir()
SECRETS_FILE = DATA_DIR / "secrets.json"
MASTER_PASSWORD = None

def load_secrets():
    global MASTER_PASSWORD
    # Priority 1: Environment Variable (Dev override)
    if os.environ.get("PRV_MASTER_PASSWORD"):
        MASTER_PASSWORD = os.environ.get("PRV_MASTER_PASSWORD")
        logging.info("Loaded Master Password from Environment Variable.")
        return

    # Priority 2: Secrets File
    if SECRETS_FILE.exists():
        try:
            with open(SECRETS_FILE, "r") as f:
                data = json.load(f)
                MASTER_PASSWORD = data.get("master_password")
                logging.info(f"Loaded Master Password from: {SECRETS_FILE}")
        except Exception as e:
            logging.error(f"Failed to load secrets file: {e}")

load_secrets()
# -------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("--- Application Startup ---")
    
    # 1. Start external services
    service_manager.auto_start_services()
    
    # 2. Check if Setup is Done
    # FIX: Check flag in DATA_DIR
    setup_flag_path = DATA_DIR / ".setup_complete"
    
    if setup_flag_path.exists() and MASTER_PASSWORD:
        logging.info("Setup complete. Initializing Core Services.")
        
        # Initialize DB & Encryption
        db.create_db_and_tables()
        db_manager.initialize_encryption(MASTER_PASSWORD)
        
        # Start Scheduler
        scheduler.start_scheduler_if_needed()
    else:
        logging.warning("Setup not complete or Password missing. App in SETUP MODE.")
    
    yield
    
    logging.info("--- Application Shutdown ---")
    if scheduler.scheduler_task:
        scheduler.scheduler_task.cancel()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(contacts_router.router, prefix="/api")
app.include_router(drafts_router.router, prefix="/api")
app.include_router(inbox_router.router, prefix="/api")
app.include_router(system_router.router, prefix="/api")
app.include_router(groups_router.router, prefix="/api")
app.include_router(setup_router.router, prefix="/api")

# Mount Static Files
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
async def root():
    """
    Intelligent Routing:
    - If setup is done -> Go to App
    - If setup is missing -> Go to Wizard
    """
    # FIX: Check flag in DATA_DIR
    setup_flag_path = DATA_DIR / ".setup_complete"
    
    # Hot-Reload Secrets if just created
    global MASTER_PASSWORD
    if setup_flag_path.exists() and MASTER_PASSWORD is None:
        load_secrets()
    
    token_path = DATA_DIR / "token.json"
    if setup_flag_path.exists() and MASTER_PASSWORD and token_path.exists():
        return FileResponse(FRONTEND_DIR / "app.html")
    else:
        return FileResponse(FRONTEND_DIR / "index.html")