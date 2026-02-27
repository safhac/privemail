# src/core/config.py

from pathlib import Path
from core.path_utils import get_data_dir

def get_setup_complete_flag_path() -> Path:
    """Returns the path to the setup complete flag."""
    return get_data_dir() / ".setup_complete"

# For backwards compatibility, compute at import time
# (but this is now a function call instead of hardcoded path)
SETUP_COMPLETE_FLAG_PATH = get_setup_complete_flag_path()


# --- Default Model ---
DEFAULT_OLLAMA_MODEL = "qwen2:0.5b"

# --- Model Resource Requirements ---
# Hardcoded requirements (CPU cores, RAM GB) for specific models
MODEL_REQUIREMENTS = {
    "gemma2:2b": (4, 8),
    "qwen2:0.5b": (2, 4),
    "qwen2:7b": (6, 16),
    "qwen3": (6, 16),
    "llama3": (6, 16),
}

# Default requirement if model is not in the list
DEFAULT_MODEL_REQ = (4, 8)