import os
import sys
import webbrowser
import uvicorn
import multiprocessing
from pathlib import Path

# Add current directory to sys.path so 'import core' and 'import routes' work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import main app
import main
from core.path_utils import get_app_root

def start_server():
    """Starts the Uvicorn server."""
    # Run Uvicorn with reload=True for easier open source dev
    uvicorn.run(
        "main:app", 
        host="127.0.0.1", 
        port=8000, 
        log_level="info",
        reload=True, 
        workers=1
    )

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    # Set root to the parent of src (the project root)
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)
    
    print("--- Starting Privemail (Open Source) ---")
    print(f"Project Root: {project_root}")
    
    # Open Browser
    webbrowser.open("http://127.0.0.1:8000")

    # Start Server
    start_server()