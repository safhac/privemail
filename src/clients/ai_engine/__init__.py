# src/clients/ai_engine/__init__.py

from .base import chat_completion, AI_LOCK
from .system import get_system_resources, check_model_compatibility, check_ollama_status
from .management import pull_model, list_installed_models, list_local_models
from .generation import generate_text, rewrite_paragraph_for_tone, analyze_correspondent, generate_draft_reply, unload_model
