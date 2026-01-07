from core.path_utils import get_app_root
import main
import os
import sys
import webbrowser
import uvicorn
import multiprocessing
import subprocess
from pathlib import Path

# Add current directory to sys.path so 'import core' and 'import routes' work
# This allows 'import main' to succeed immediately in this script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import main app logic and utils


def relaunch_in_uv_venv():
    """
    If running with the system Python, try to switch to the 'uv' .venv automatically.
    """
    # If we are already in a venv (prefix != base_prefix), do nothing.
    if sys.prefix != sys.base_prefix:
        return

    # Look for the standard uv .venv directory
    # (Assumes .venv is in the project root, two levels up from src/launcher.py)
    root_dir = Path(__file__).resolve().parent.parent
    venv_python = root_dir / ".venv" / "bin" / "python"

    if sys.platform == "win32":
        venv_python = root_dir / ".venv" / "Scripts" / "python.exe"

    if venv_python.exists():
        print(f"--- Switching to uv environment: {venv_python} ---")
        try:
            # Re-run this script using the venv python
            subprocess.call([str(venv_python), __file__] + sys.argv[1:])
            sys.exit()
        except Exception as e:
            print(f"Failed to auto-switch to venv: {e}")


def start_server():
    """Starts the Uvicorn server."""
    # CRITICAL FIX: Add 'src' to PYTHONPATH for the Uvicorn subprocess.
    # When 'reload=True', Uvicorn spawns a new process that doesn't inherit
    # the sys.path modification above. We must inject it via environment vars.
    src_path = os.path.dirname(os.path.abspath(__file__))
    current_pythonpath = os.environ.get("PYTHONPATH", "")

    # Prepend src path to PYTHONPATH
    os.environ["PYTHONPATH"] = src_path + os.pathsep + current_pythonpath

    # Run Uvicorn using the string import syntax ("main:app") so reloading works
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=True,
        workers=1
    )


if __name__ == "__main__":
    relaunch_in_uv_venv()

    # Required for Windows (PyInstaller support)
    multiprocessing.freeze_support()

    # Set working directory to the project root (one level up from src)
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)

    print("--- Starting Privemail (Open Source) ---")
    print(f"Project Root: {project_root}")

    # Open Browser
    webbrowser.open("http://127.0.0.1:8000")

    # Start Server
    start_server()
