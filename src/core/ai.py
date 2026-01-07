import ollama

# Recommended Model for Hebrew
MODEL = "qwen2.5:3b" 

async def rewrite_text(text: str, command: str, language: str = "en") -> str:
    """
    Sends text to LLM with language awareness.
    """
    
    # 1. Define Persona based on Language
    if language == 'he':
        persona = "You are a Senior Attorney in Israel (עורך דין בכיר). You write in professional, legal Hebrew."
        lang_instruction = "IMPORTANT: Output the result in HEBREW (עברית) only."
    else:
        persona = "You are a Senior Partner at a top law firm."
        lang_instruction = "Output in English."

    # 2. Define Prompts
    prompts = {
        "legalize": {
            "en": "Rewrite to be strictly formal, defensive, and legally precise.",
            "he": "שכתב את הטקסט לשפה משפטית רשמית, מדויקת ומגנה (Legal Hebrew)."
        },
        "improve": {
            "en": "Rewrite to be clearer and fix grammar.",
            "he": "שפר את הניסוח, תקן שגיאות דקדוק והפוך את הטקסט למקצועי יותר."
        }
    }
    
    # Get instruction safely
    instruction_map = prompts.get(command, prompts["improve"])
    specific_instruction = instruction_map.get(language, instruction_map["en"])
    
    system_prompt = f"""
    {persona}
    Task: {specific_instruction}
    
    CRITICAL RULES:
    1. {lang_instruction}
    2. Do NOT add conversational filler (e.g. "Here is the translation").
    3. Maintain the original legal intent perfectly.
    """
    
    try:
        response = await ollama.AsyncClient().chat(
            model=MODEL,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': text}
            ]
        )
        return response['message']['content'].strip()
    except Exception as e:
        print(f"❌ AI Error: {e}")
        return f"[Error: AI Connection Failed. Is Ollama running?]"
    
    
async def generate_response(instruction, context, tone, language="en"):
    
    tone_map = {
        "aggressive": "Be firm, uncompromising, and legally aggressive.",
        "neutral": "Be objective, calm, and matter-of-fact.",
        "apologetic": "Be polite and conciliatory but protect legal liability."
    }
    selected_tone = tone_map.get(tone, "Be professional.")

    system_prompt = f"""
    You are a Senior Attorney.
    Task: Draft a legal response based on the provided CONTEXT document.
    Tone: {selected_tone}
    Language: {language} (Output ONLY in this language).
    
    --- CONTEXT DOCUMENT (The document we are replying to) ---
    {context[:3000]}  # Truncate to fit context window
    ---------------------------------------------------------
    """
    
    # ... call ollama ...