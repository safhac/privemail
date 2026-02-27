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
    - Prod Mode: Platform-specific user data directory
      - Windows: %APPDATA% / Privemail
      - macOS: ~/Library/Application Support / Privemail
      - Linux: ~/.local/share / Privemail
    """
    if getattr(sys, 'frozen', False):
        # PROD: Use platform-specific user data directory (No Admin needed!)
        if sys.platform == "win32":
            app_data = Path(os.getenv('APPDATA')) / "Privemail"
        elif sys.platform == "darwin":
            # macOS
            app_data = Path.home() / "Library" / "Application Support" / "Privemail"
        else:
            # Linux and other Unix-like systems
            app_data = Path.home() / ".local" / "share" / "Privemail"
        app_data.mkdir(parents=True, exist_ok=True)
        return app_data
    else:
        # DEV: Use local folder
        app_data = Path(__file__).resolve().parent.parent / "app_data"
        app_data.mkdir(exist_ok=True)
        return app_data