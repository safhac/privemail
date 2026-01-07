# src/core/config.py

from pathlib import Path

SETUP_COMPLETE_FLAG_PATH = Path("app_data/.setup_complete")


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