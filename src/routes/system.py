import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from typing import List, Dict
from sqlalchemy.orm import Session

from models.schemas import (
    GenerationRequest, 
    ModelItem, 
    SettingsUpdateRequest,
    ModelSettingRequest
)
import clients.ollama as ollama_client
from database.db import get_db, Setting
from scheduler import _get_setting, _set_setting

router = APIRouter(
    tags=["System & Models"],
)

# --- System Status ---

@router.get("/status")
async def get_status():
    is_running = await ollama_client.check_ollama_status()
    if is_running:
        return {"status": "Ollama server is running"}
    else:
        raise HTTPException(status_code=503, detail="Ollama server is offline")

@router.post("/system/unload")
async def unload_ai_model():
    """Forcefully unloads the AI model to free resources."""
    await ollama_client.unload_model()
    return {"status": "success", "message": "AI Model Unload Signal Sent"}

# --- Settings Endpoints ---

@router.get("/settings", response_model=Dict[str, str])
async def get_all_settings(db: Session = Depends(get_db)):
    settings = db.query(Setting).all()
    return {s.key: s.value for s in settings}

@router.post("/settings")
async def update_settings(
    request: SettingsUpdateRequest, 
    db: Session = Depends(get_db)
):
    try:
        for item in request.settings:
            _set_setting(db, item.key, item.value)
        db.commit()
        return {"status": "success", "message": "Settings updated."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {e}")

@router.post("/settings/model")
async def set_default_model(
    request: ModelSettingRequest,
    db: Session = Depends(get_db)
):
    try:
        _set_setting(db, "ollama_model", request.model_name)
        return {"status": "success", "message": f"Default model set to {request.model_name}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to set model: {e}")

@router.post("/settings/pause")
async def toggle_pause(enabled: bool, db: Session = Depends(get_db)):
    """Pauses or Resumes the background scheduler."""
    # 'enabled' here means "is pause enabled?" (True = Paused)
    _set_setting(db, "scheduler_paused", str(enabled).lower())
    return {"status": "success", "paused": enabled}

# --- Model & AI Endpoints ---

@router.get("/models", response_model=List[str])
async def get_installed_models_list():
    try:
        models = await ollama_client.list_installed_models()
        return models
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/list/{selected_model}", response_model=List[ModelItem])
async def get_models(selected_model: str):
    if selected_model.lower() in ["null", "undefined", "none"]:
        selected_model = "" 
    models = await ollama_client.list_local_models(selected_model)
    return models

@router.post("/generate", response_class=PlainTextResponse)
async def post_generate(request: GenerationRequest):
    try:
        output = await ollama_client.generate_text(request)
        return output
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))