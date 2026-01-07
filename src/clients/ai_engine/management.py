import logging
import sys
from typing import List
from .base import client, OLLAMA_LOCK
from .system import check_model_compatibility
from models.schemas import ModelItem

async def pull_model(model_name: str) -> bool:
    is_compatible, msg = check_model_compatibility(model_name)
    if not is_compatible:
        logging.error(f"Cannot pull model: {msg}")
        return False
    async with OLLAMA_LOCK:
        logging.info(f"OLLAMA_LOCK acquired by pull_model({model_name})")
        try:
            logging.info(f"Pulling model: {model_name}. This may take a while...")
            async for progress in client.pull(model_name, stream=True):
                if 'status' in progress and progress['status'] == 'success':
                    logging.info(f"Successfully pulled model {model_name}.")
                    return True
            logging.info(f"Model {model_name} is already up to date.")
            return True
        except Exception as e:
            logging.error(f"Failed to pull model {model_name}: {e}")
            return False
        finally:
            logging.info(f"OLLAMA_LOCK released by pull_model({model_name})")

async def list_installed_models() -> List[str]:
    try:
        response = await client.list()
        # Handle both list-of-dicts and dict-with-models-key
        models_list = response.get('models', response)
        models = [model['model'] for model in models_list]
        logging.debug(f"Found {len(models)} installed models.")
        return models
    except Exception as e:
        logging.error(f"Failed to list installed models: {e}")
        return []

async def list_local_models(selected_model: str) -> List[ModelItem]:
    try:
        response = await client.list()
        model_items = []
        models_list = response.get('models', response)
        
        for model in models_list:
            name = model['model']
            is_sel = (name == selected_model)
            color = "Green" if is_sel else "Dark Grey"
            
            model_items.append(ModelItem(
                name=name,
                is_installed=True, 
                is_selected=is_sel,
                status_color=color
            ))
            
        logging.debug(f"Successfully processed {len(model_items)} models.")
        return model_items
        
    except Exception as e:
        logging.error(f"CRITICAL ERROR during model list processing: {e}", file=sys.stderr)
        return []