import ollama
from typing import List, Tuple, Dict, Any
from httpx import ConnectError
from models.schemas import GenerationRequest, ModelItem
import sys
import logging
import psutil
import math
import asyncio
import json

from db import Contact

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from core.config import (
    MODEL_REQUIREMENTS, 
    DEFAULT_MODEL_REQ,
    DEFAULT_OLLAMA_MODEL
)
# Global Concurrency Lock
OLLAMA_LOCK = asyncio.Lock()

# Use a single async client instance for efficiency
client = ollama.AsyncClient(host='http://localhost:11434')

# --- System Resource Utilities ---
def get_system_resources() -> dict:
    mem = psutil.virtual_memory()
    total_mem_gb = math.ceil(mem.total / (1024**3))
    cpu_cores = psutil.cpu_count(logical=False)
    logging.debug(f"System resources: {cpu_cores} physical cores, {total_mem_gb}GB RAM")
    return {"cpu_cores": cpu_cores, "total_mem_gb": total_mem_gb}

def check_model_compatibility(model_name: str) -> Tuple[bool, str]:
    MODEL_REQUIREMENTS = {
        "gemma2:2b": (4, 8),
        "qwen2:0.5b": (2, 4),
        "qwen2:7b": (6, 16),
        "qwen3": (6, 16),
        "llama3": (6, 16),
    }
    DEFAULT_REQ = (4, 8) 
    req = DEFAULT_REQ
    for key, requirements in MODEL_REQUIREMENTS.items():
        if key in model_name:
            req = requirements
            break
    required_cores, required_ram = req
    system_res = get_system_resources()
    sys_cores = system_res['cpu_cores']
    sys_ram = system_res['total_mem_gb']
    if sys_cores < required_cores or sys_ram < required_ram:
        msg = (
            f"Insufficient resources for {model_name}. "
            f"Requires: {required_cores} cores / {required_ram}GB RAM. "
            f"System has: {sys_cores} cores / {sys_ram}GB RAM."
        )
        logging.warning(msg)
        return (False, msg)
    logging.info(f"System meets requirements for {model_name}.")
    return (True, msg)

# --- Model Management Functions ---
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

# --- NEW: Unload Function ---
async def unload_model() -> bool:
    """Forces Ollama to unload the model from memory, freeing CPU/RAM."""
    try:
        # Sending an empty request with keep_alive=0 triggers unload
        await client.generate(model="", keep_alive=0)
        logging.info("Ollama model unloaded successfully.")
        return True
    except Exception as e:
        # It often throws 404 because model="" is invalid, but the side effect works.
        logging.info(f"Ollama unload signal sent (Error expected, ignoring): {e}")
        return True

# --- AI Processing Functions ---

async def generate_text(request: GenerationRequest) -> str:
    system_prompt = f"""
    You are an assistant. Your task is to refine the user's input text.
    Follow these instructions precisely:
    1. Goal: {request.goal}
    2. Tone: {request.tone}
    3. Tone Strength (0.0=subtle, 1.0=strong): {request.tone_dial_value}
    4. Ad-hoc Instructions: {request.ad_hoc_instruction}
    
    Refine the following text based *only* on these rules.
    """
    async with OLLAMA_LOCK:
        logging.info(f"OLLAMA_LOCK acquired by generate_text()")
        try:
            response = await client.chat(
                model=request.model_name,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': request.input_text}
                ],
                options={"num_predict": 500} # Limit output size
            )
            return response['message']['content']
        except Exception as e:
            logging.error(f"Error generating text: {e}")
            return f"Error generating text: {str(e)}"
        finally:
            logging.info(f"OLLAMA_LOCK released by generate_text()")

async def rewrite_paragraph_for_tone(
    system_prompt: str,
    paragraph: str, 
    model: str = DEFAULT_OLLAMA_MODEL
) -> str:
    async with OLLAMA_LOCK:
        logging.info(f"OLLAMA_LOCK acquired by rewrite_paragraph_for_tone()")
        try:
            response = await client.chat(
                model=model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': paragraph}
                ],
                options={"num_predict": 500} # Limit output size
            )
            return response['message']['content']
        except Exception as e:
            logging.error(f"Error rewriting text: {e}")
            return f"Error rewriting text: {str(e)}"
        finally:
            logging.info(f"OLLAMA_LOCK released by rewrite_paragraph_for_tone()")

async def analyze_correspondent(email_body: str) -> Dict[str, Any]:
    system_prompt = f"""
    You are an expert email analyst. Analyze the user's email text.
    You MUST return *only* a single, valid JSON object with three keys:
    1. "correspondent_tone": (e.g., "Formal", "Casual", "Urgent", "Anxious")
    2. "correspondent_goal": (A brief summary of what the sender wants, e.g., "Requesting a meeting")
    3. "correspondent_evidence": (A direct quote from the text that supports your analysis)

    Do not provide any preamble, explanation, or other text.
    """
    default_response = {
        "correspondent_tone": "N/A",
        "correspondent_goal": "Analysis Failed",
        "correspondent_evidence": "Could not parse LLM response"
    }
    async with OLLAMA_LOCK:
        logging.info("OLLAMA_LOCK acquired by analyze_correspondent()")
        try:
            # ADDED: Timeout logic
            response = await asyncio.wait_for(
                client.chat(
                    model=DEFAULT_OLLAMA_MODEL, 
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': email_body}
                    ],
                    options={"temperature": 0.0, "num_predict": 300},
                    format="json"
                ),
                timeout=60.0 # 60 second timeout
            )
            
            raw_response = response['message']['content']
            logging.info("OLLAMA_CLIENT: Analysis received, attempting to parse JSON.")
            analysis_result = json.loads(raw_response)
            if all(key in analysis_result for key in default_response.keys()):
                return analysis_result
            else:
                logging.warning("OLLAMA_CLIENT: Analysis JSON missing required keys.")
                return default_response

        except asyncio.TimeoutError:
            logging.error("OLLAMA_CLIENT: Analysis timed out (stuck). Skipping.")
            return default_response
        except json.JSONDecodeError:
            logging.error(f"OLLAMA_CLIENT: Failed to decode JSON from response: {raw_response}")
            return default_response
        except Exception as e:
            logging.error(f"Error in analyze_correspondent: {e}")
            return default_response
        finally:
            logging.info("OLLAMA_LOCK released by analyze_correspondent()")

async def generate_draft_reply(
    context: str, 
    contact: Contact, 
    style_sample_text: str = None
) -> str | None:
    if not contact.auto_draft_enabled:
        logging.info(f"OLLAMA_CLIENT: Auto-draft disabled for {contact.email_address}. Skipping generation.")
        return None

    style_prompt = "Your response must have a Formal Professional style."
    if style_sample_text:
        style_prompt = f"Your response must match the style of these samples:\n---\n{style_sample_text}\n---"
    elif contact.tone:
        style_prompt = f"Your response must have a {contact.tone} tone."

    system_prompt = f"""
    You are a professional email assistant. Your sole task is to write a draft reply to the email provided by the user.
    
    RULES:
    1.  You must draft *only* the body of the reply.
    2.  Do NOT include a greeting (like "Hi John,").
    3.  Do NOT include a sign-off (like "Best," or "Regards,").
    4.  Do NOT include your own name.
    5.  Do NOT repeat the original email.
    6.  The user's goal is to be helpful and address the sender's needs.
    7.  {style_prompt}
    
    Respond with *only* the draft.
    """
    
    user_content = f"""
    Here is the email to reply to:
    ---
    {context}
    ---
    """
    
    async with OLLAMA_LOCK:
        logging.info("OLLAMA_LOCK acquired by generate_draft_reply()")
        try:
            # ADDED: Timeout logic
            response = await asyncio.wait_for(
                client.chat(
                    model=DEFAULT_OLLAMA_MODEL,
                    messages=[
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': user_content}
                    ],
                    options={"num_predict": 1000} # prevent infinite loops
                ),
                timeout=90.0 # 90 second timeout
            )
            logging.info("OLLAMA_CLIENT: Draft generation complete.")
            return response['message']['content'].strip()
        except asyncio.TimeoutError:
            logging.error("OLLAMA_CLIENT: Draft Generation timed out. Skipping.")
            return None
        except Exception as e:
            logging.error(f"Error in generate_draft_reply: {e}")
            return f"Error generating draft: {e}"
        finally:
            logging.info("OLLAMA_LOCK released by generate_draft_reply()")

# --- Non-Locked Functions (Unchanged) ---
async def check_ollama_status() -> bool:
    try:
        await client.list()
        logging.debug("Connection to Ollama successful.")
        return True
    except ConnectError:
        logging.warning("Ollama connection failed.")
        return False
    except Exception as e:
        logging.error(f"Ollama status check error: {e}")
        return False

async def list_installed_models() -> List[str]:
    try:
        response = await client.list()
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