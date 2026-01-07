import os
import httpx
import ollama
import asyncio
import logging
from database.db import SessionLocal, Setting

# Global Lock to prevent frying your CPU
AI_LOCK = asyncio.Lock()


def _get_config():
    """Fetch AI settings from DB on every call to support hot-swapping."""
    session = SessionLocal()
    try:
        # Defaults
        provider = "ollama"
        base_url = "http://localhost:11434/v1"
        api_key = "ollama"  # Dummy key for local

        # Fetch overrides
        settings = {s.key: s.value for s in session.query(Setting).all()}

        if "ai_provider" in settings:
            provider = settings["ai_provider"]
        if "ai_base_url" in settings:
            base_url = settings["ai_base_url"]
        if "ai_api_key" in settings:
            api_key = settings["ai_api_key"]

        return provider, base_url, api_key
    finally:
        session.close()


async def chat_completion(model: str, messages: list, json_mode: bool = False, options: dict = None):
    """
    Universal wrapper that routes requests to either Native Ollama or 
    an OpenAI-Compatible API (llama.cpp, LM Studio, OpenRouter).
    """
    provider, base_url, api_key = _get_config()

    # 1. NATIVE OLLAMA (Kept for backward compatibility/ease)
    if provider == "ollama":
        # We use the python lib for native features like 'pull' management
        client = ollama.AsyncClient(host=base_url.replace("/v1", ""))
        format_val = "json" if json_mode else None

        # Map generic 'options' to Ollama specific options if needed
        # (Ollama python lib handles most keys automatically)
        return await client.chat(
            model=model,
            messages=messages,
            format=format_val,
            options=options
        )

    # 2. GENERIC OPENAI-COMPATIBLE (The new feature)
    else:
        async with httpx.AsyncClient(timeout=120.0) as http_client:
            payload = {
                "model": model,
                "messages": messages,
                "temperature": options.get("temperature", 0.7) if options else 0.7
            }

            if json_mode:
                payload["response_format"] = {"type": "json_object"}

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            try:
                response = await http_client.post(
                    f"{base_url}/chat/completions",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()

                # Normalize response to look like Ollama's object
                # so the rest of the app doesn't break
                return {
                    'message': {
                        'content': data['choices'][0]['message']['content']
                    }
                }
            except Exception as e:
                logging.error(f"AI Provider Error ({base_url}): {e}")
                raise e
