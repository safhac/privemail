import os
import sys
import webbrowser
import uvicorn
import multiprocessing
from core.path_utils import get_app_root

import main

def start_server():
    """Starts the Uvicorn server."""
    # Determine if we should reload (only in dev mode)
    is_frozen = getattr(sys, 'frozen', False)
    
    # Run Uvicorn
    # Note: In frozen mode, 'main:app' string loading might fail unless 
    # main is imported, so we import it directly in the spec or ensure path is correct.
    # A safer way for PyInstaller is to pass the app object directly if possible, 
    # but string reference works if main.py is bundled correctly.
    uvicorn.run(
        main.app, 
        host="127.0.0.1", 
        port=8000, 
        log_level="info",
        reload=False, # Must be False when passing the app object
        workers=1
    )

if __name__ == "__main__":
    # PyInstaller fix for multiprocessing on Windows
    multiprocessing.freeze_support()
    
    # 1. Change Working Directory to the App Root
    # This ensures relative paths like "app_data/" work correctly
    root_dir = get_app_root()
    os.chdir(root_dir)
    
    # 2. Open Browser (delayed slightly to allow server boot)
    print("--- Starting Privemail ---")
    print(f"Root Directory: {root_dir}")
    
    # Launch browser in a separate thread/timer would be cleaner, 
    # but putting it before run() works because run() blocks.
    # We use a timer logic or just fire it immediately.
    webbrowser.open("http://127.0.0.1:8000")

    # 3. Start Server (Blocks until quit)
    start_server()