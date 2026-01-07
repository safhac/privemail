# src/launcher.py

import sys
import os
import subprocess
from pathlib import Path
import multiprocessing

# ... existing imports ...


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
        # Re-run this script using the venv python
        try:
            subprocess.call([str(venv_python), __file__] + sys.argv[1:])
            sys.exit()
        except Exception as e:
            print(f"Failed to auto-switch to venv: {e}")


if __name__ == "__main__":
    relaunch_in_uv_venv()

    # ... The rest of your existing launcher code (multiprocessing, etc.) ...
    multiprocessing.freeze_support()
    # ...
