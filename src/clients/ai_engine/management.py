import logging
import sys
import httpx
import ollama
from typing import List
from .base import AI_LOCK, _get_config
from .system import check_model_compatibility
from models.schemas import ModelItem


async def pull_model(model_name: str) -> bool:
    provider, base_url, _ = _get_config()
    if provider != "ollama":
        logging.info("Skipping pull: Not supported for generic providers.")
        return True  # Pretend success

    # Existing Ollama Pull Logic
    try:
        client = ollama.AsyncClient(host=base_url.replace("/v1", ""))
        async for progress in client.pull(model_name, stream=True):
            pass
        return True
    except Exception as e:
        logging.error(f"Pull failed: {e}")
        return False


async def list_installed_models() -> List[str]:
    provider, base_url, api_key = _get_config()

    try:
        if provider == "ollama":
            # Native Ollama List
            client = ollama.AsyncClient(host=base_url.replace("/v1", ""))
            response = await client.list()
            models_list = response.get('models', response)
            return [model['model'] for model in models_list]

        else:
            # Generic OpenAI /v1/models List
            async with httpx.AsyncClient(timeout=10.0) as http:
                headers = {"Authorization": f"Bearer {api_key}"}
                resp = await http.get(f"{base_url}/models", headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    # OpenRouter/OpenAI usually return { data: [ {id: "name"}, ... ] }
                    return [m['id'] for m in data.get('data', [])]
                return ["custom-model (List failed)"]

    except Exception as e:
        logging.error(f"Failed to list models: {e}")
        return []


async def list_local_models(selected_model: str) -> List[ModelItem]:
    models = await list_installed_models()
    return [
        ModelItem(
            name=m,
            is_installed=True,
            is_selected=(m == selected_model),
            status_color="Green" if m == selected_model else "Dark Grey"
        ) for m in models
    ]
