import psutil
import math
import logging
from typing import Tuple
from httpx import ConnectError
from .base import client
from core.config import MODEL_REQUIREMENTS, DEFAULT_MODEL_REQ

def get_system_resources() -> dict:
    mem = psutil.virtual_memory()
    total_mem_gb = math.ceil(mem.total / (1024**3))
    cpu_cores = psutil.cpu_count(logical=False)
    logging.debug(f"System resources: {cpu_cores} physical cores, {total_mem_gb}GB RAM")
    return {"cpu_cores": cpu_cores, "total_mem_gb": total_mem_gb}

def check_model_compatibility(model_name: str) -> Tuple[bool, str]:
    req = DEFAULT_MODEL_REQ
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