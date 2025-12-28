import sys
import os
from pathlib import Path

def get_app_root() -> Path:
    """Returns the directory where the executable/script lives."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).resolve().parent.parent

def get_data_dir() -> Path:
    """
    Returns the writable directory for user data.
    - Dev Mode: Project root / app_data
    - Prod Mode: %APPDATA% / Privemail
    """
    if getattr(sys, 'frozen', False):
        # PROD: Use User's AppData folder (No Admin needed!)
        app_data = Path(os.getenv('APPDATA')) / "Privemail"
        app_data.mkdir(parents=True, exist_ok=True)
        return app_data
    else:
        # DEV: Use local folder
        app_data = Path(__file__).resolve().parent.parent / "app_data"
        app_data.mkdir(exist_ok=True)
        return app_data