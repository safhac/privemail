import json
import logging
from typing import Dict, Any
# client: the shared AsyncClient instance for Ollama API calls
from .base import chat_completion, AI_LOCK, _get_config
import ollama
from models.schemas import GenerationRequest
from database.db import Contact
from core.config import DEFAULT_OLLAMA_MODEL


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
    async with AI_LOCK:
        logging.info(f"AI_LOCK acquired by generate_text()")
        try:
            response = await chat_completion(
                model=request.model_name,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': request.input_text}
                ]
            )
            return response['message']['content']
        except Exception as e:
            logging.error(f"Error generating text: {e}")
            return f"Error generating text: {str(e)}"
        finally:
            logging.info(f"AI_LOCK released by generate_text()")


async def rewrite_paragraph_for_tone(
    system_prompt: str,
    paragraph: str,
    model: str = DEFAULT_OLLAMA_MODEL
) -> str:
    async with AI_LOCK:
        logging.info(f"AI_LOCK acquired by rewrite_paragraph_for_tone()")
        try:
            response = await chat_completion(
                model=model,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': paragraph}
                ]
            )
            return response['message']['content']
        except Exception as e:
            logging.error(f"Error rewriting text: {e}")
            return f"Error rewriting text: {str(e)}"
        finally:
            logging.info(
                f"AI_LOCK released by rewrite_paragraph_for_tone()")


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
    async with AI_LOCK:
        logging.info("AI_LOCK acquired by analyze_correspondent()")
        try:
            response = await chat_completion(
                model=DEFAULT_OLLAMA_MODEL,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': email_body}
                ],
                options={"temperature": 0.0},
                json_mode=True
            )
            raw_response = response['message']['content']
            logging.info(
                "OLLAMA_CLIENT: Analysis received, attempting to parse JSON.")
            analysis_result = json.loads(raw_response)
            if all(key in analysis_result for key in default_response.keys()):
                return analysis_result
            else:
                logging.warning(
                    "OLLAMA_CLIENT: Analysis JSON missing required keys.")
                return default_response
        except json.JSONDecodeError:
            logging.error(
                f"OLLAMA_CLIENT: Failed to decode JSON from response: {raw_response}")
            return default_response
        except Exception as e:
            logging.error(f"Error in analyze_correspondent: {e}")
            return default_response
        finally:
            logging.info("AI_LOCK released by analyze_correspondent()")


async def generate_draft_reply(
    context: str,
    contact: Contact,
    style_sample_text: str = None
) -> str | None:
    if not contact.auto_draft_enabled:
        logging.info(
            f"OLLAMA_CLIENT: Auto-draft disabled for {contact.email_address}. Skipping generation.")
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

    async with AI_LOCK:
        logging.info("AI_LOCK acquired by generate_draft_reply()")
        try:
            response = await chat_completion(
                model=DEFAULT_OLLAMA_MODEL,
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_content}
                ]
            )
            logging.info("OLLAMA_CLIENT: Draft generation complete.")
            return response['message']['content'].strip()
        except Exception as e:
            logging.error(f"Error in generate_draft_reply: {e}")
            return f"Error generating draft: {e}"
        finally:
            logging.info("AI_LOCK released by generate_draft_reply()")


async def unload_model(model_name: str):
    """
    Tells the AI engine to free the model from RAM.
    Only works for Ollama (using keep_alive=0).
    """
    provider, base_url, _ = _get_config()

    if provider == "ollama":
        try:
            # To unload in Ollama, send an empty request with keep_alive=0
            local_client = ollama.AsyncClient(host=base_url.replace("/v1", ""))
            await local_client.chat(model=model_name, messages=[], keep_alive=0)
        except Exception as e:
            logging.error(f"Failed to unload model: {e}")
    else:
        pass
