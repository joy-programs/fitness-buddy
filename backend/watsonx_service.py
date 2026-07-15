"""
watsonx_service.py — IBM watsonx.ai / Granite integration
----------------------------------------------------------
This module is the ONLY place that talks to IBM watsonx.ai.
All route logic stays in the router files; this file handles:
  - Loading IBM Cloud credentials from environment variables
  - Creating and caching the WatsonxAI client
  - Building prompts (system + user message)
  - Calling the Granite model
  - Parsing / validating structured JSON responses from the model
  - Returning clean strings or dicts to the caller

Environment variables required (set in .env):
  IBM_API_KEY          — IBM Cloud API key
  WATSONX_PROJECT_ID   — watsonx.ai project ID
  WATSONX_URL          — regional service URL
  GRANITE_MODEL_ID     — model deployment ID
"""

import os
import json
import logging
import re
from functools import lru_cache
from typing import Optional, Any

from dotenv import load_dotenv

# Load .env file values into os.environ
load_dotenv()

logger = logging.getLogger(__name__)

# ── Lazy IBM client — created once on first use ───────────────
_client = None


def _get_client():
    """
    Return a cached ibm_watsonx_ai.APIClient instance.
    Raises a clear RuntimeError if credentials are missing.
    """
    global _client
    if _client is not None:
        return _client

    api_key    = os.getenv("IBM_API_KEY", "").strip()
    url        = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com").strip()

    if not api_key:
        raise RuntimeError(
            "IBM_API_KEY is not set. "
            "Copy .env.example to .env and add your IBM Cloud API key."
        )

    # ibm_watsonx_ai — imported here so the rest of the app still loads
    # even if the package is not installed (gives a clear error on first use)
    try:
        from ibm_watsonx_ai import APIClient, Credentials
    except ImportError as e:
        raise RuntimeError(
            "ibm-watsonx-ai package is not installed. Run: pip install ibm-watsonx-ai"
        ) from e

    credentials = Credentials(url=url, api_key=api_key)
    _client = APIClient(credentials)
    logger.info("IBM watsonx.ai client initialised successfully.")
    return _client


# ── Core text generation function ─────────────────────────────

def generate_text(
    system_prompt: str,
    user_message:  str,
    max_new_tokens: int = 1024,
    temperature:    float = 0.7,
) -> str:
    """
    Send a prompt to the IBM Granite model and return the text response.

    Args:
        system_prompt  : The Fitness Buddy system prompt (from agent_instructions)
        user_message   : The actual user request / question
        max_new_tokens : Maximum tokens to generate (default 1024)
        temperature    : Creativity level 0.0–1.0 (0.7 is a good balance)

    Returns:
        Generated text string.

    Raises:
        RuntimeError if credentials are missing or the model call fails.
    """
    project_id = os.getenv("WATSONX_PROJECT_ID", "").strip()
    model_id   = os.getenv("GRANITE_MODEL_ID", "ibm/granite-3-3-8b-instruct").strip()

    if not project_id:
        raise RuntimeError(
            "WATSONX_PROJECT_ID is not set. Add it to your .env file."
        )

    client = _get_client()

    try:
        from ibm_watsonx_ai.foundation_models import ModelInference
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as Params
    except ImportError as e:
        raise RuntimeError("ibm-watsonx-ai package components not found.") from e

    # ── Construct the messages list (chat format) ─────────────
    # IBM Granite 3.x instruct models use the standard chat messages format.
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_message},
    ]

    # Generation parameters
    gen_params = {
        Params.MAX_NEW_TOKENS: max_new_tokens,
        Params.TEMPERATURE:    temperature,
        Params.REPETITION_PENALTY: 1.05,
    }

    # ── Call the model ────────────────────────────────────────
    model = ModelInference(
        model_id=model_id,
        credentials=client.credentials,
        project_id=project_id,
        params=gen_params,
    )

    logger.debug("Sending request to Granite model: %s", model_id)
    response = model.chat(messages=messages)

    # Extract the generated text from the response
    # Structure: response["choices"][0]["message"]["content"]
    try:
        generated = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        logger.error("Unexpected model response structure: %s", response)
        raise RuntimeError(f"Unexpected model response: {e}") from e

    return generated.strip()


# ── Structured JSON generation ────────────────────────────────

def generate_json(
    system_prompt: str,
    user_message:  str,
    max_new_tokens: int = 1500,
) -> Any:
    """
    Ask Granite to generate structured JSON and parse it.
    Falls back to returning the raw text if JSON parsing fails.

    The caller should add explicit JSON format instructions to
    the user_message to improve reliability.

    Returns:
        Parsed Python dict/list, or the raw string on failure.
    """
    raw = generate_text(
        system_prompt=system_prompt,
        user_message=user_message,
        max_new_tokens=max_new_tokens,
        temperature=0.4,   # lower temperature for more deterministic JSON
    )

    # Try to extract JSON from the response (model may wrap it in markdown)
    json_str = _extract_json(raw)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        logger.warning("Granite response was not valid JSON. Returning raw text.")
        return raw   # callers must handle both dict and str


def _extract_json(text: str) -> str:
    """
    Extract a JSON block from model output that may contain markdown fences.
    E.g.:  ```json\n{...}\n```  →  {…}
    """
    # Remove markdown code fences if present
    match = re.search(r"```(?:json)?\s*([\s\S]+?)```", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Try to find the first { or [ character and take from there
    for start_char in ('{', '['):
        idx = text.find(start_char)
        if idx != -1:
            # Find the matching closing character
            end_char = '}' if start_char == '{' else ']'
            end_idx = text.rfind(end_char)
            if end_idx > idx:
                return text[idx:end_idx + 1]

    return text


# ── Domain-specific generation helpers ───────────────────────

def generate_workout(
    system_prompt:  str,
    fitness_level:  str,
    fitness_goal:   str,
    duration_min:   int,
    equipment:      str,
    modification:   Optional[str] = None,
) -> Any:
    """
    Generate a structured workout plan using Granite.
    Instructs the model to respond with JSON.
    """
    mod_note = f"\n\nUser modification request: {modification}" if modification else ""

    user_message = f"""
Create a personalised home workout plan with the following details:
- Fitness level: {fitness_level}
- Primary goal: {fitness_goal.replace('_', ' ')}
- Session duration: {duration_min} minutes
- Available equipment: {equipment.replace('_', ' ')}
{mod_note}

Respond ONLY with a valid JSON object using this exact structure:
{{
  "title": "Workout plan name",
  "total_duration_min": {duration_min},
  "fitness_level": "{fitness_level}",
  "goal": "{fitness_goal}",
  "equipment": "{equipment}",
  "warm_up": [
    {{"exercise": "name", "duration": "X minutes", "instructions": "how to do it"}}
  ],
  "main_workout": [
    {{"exercise": "name", "sets": 3, "reps": "10-12", "rest_sec": 60, "instructions": "how to do it", "safety_tip": "tip"}}
  ],
  "cool_down": [
    {{"exercise": "name", "duration": "X minutes", "instructions": "how to do it"}}
  ],
  "general_tips": ["tip1", "tip2"],
  "calories_burned_estimate": "approximate range"
}}
""".strip()

    return generate_json(system_prompt, user_message, max_new_tokens=2000)


def generate_meal_suggestions(
    system_prompt:   str,
    dietary_pref:    str,
    fitness_goal:    str,
    special_request: Optional[str] = None,
) -> Any:
    """
    Generate structured meal suggestions using Granite.
    """
    sr_note = f"\nSpecial request: {special_request}" if special_request else ""

    user_message = f"""
Suggest a full day of healthy meals for someone with these preferences:
- Dietary preference: {dietary_pref.replace('_', ' ')}
- Fitness goal: {fitness_goal.replace('_', ' ')}
{sr_note}

Include plenty of common Indian food options where relevant.

Respond ONLY with a valid JSON object using this structure:
{{
  "breakfast": [
    {{"item": "food name", "description": "brief description", "protein_note": "protein content note"}}
  ],
  "lunch": [
    {{"item": "food name", "description": "brief description", "protein_note": "protein content note"}}
  ],
  "dinner": [
    {{"item": "food name", "description": "brief description", "protein_note": "protein content note"}}
  ],
  "snacks": [
    {{"item": "snack name", "description": "why it is healthy"}}
  ],
  "hydration_tip": "daily hydration advice",
  "nutrition_note": "general note about these meals and the stated goal"
}}
""".strip()

    return generate_json(system_prompt, user_message, max_new_tokens=1500)


def generate_motivation(system_prompt: str, context: Optional[str] = None) -> dict:
    """
    Generate a short motivational message and a bonus health tip.
    """
    ctx = f"User context: {context}" if context else "No specific context provided."

    user_message = f"""
{ctx}

Generate a short, genuine fitness motivation message (2-4 sentences) and one practical daily health tip.

Respond ONLY with valid JSON:
{{
  "message": "motivational message here",
  "tip": "one practical health tip here"
}}
""".strip()

    result = generate_json(system_prompt, user_message, max_new_tokens=400)

    # Ensure we always return a dict with expected keys
    if isinstance(result, dict):
        return {
            "message": result.get("message", "Keep going — every step counts!"),
            "tip":     result.get("tip", "Drink a glass of water right now."),
        }
    # Fallback if JSON parsing failed
    return {
        "message": str(result) if result else "Keep going — every step counts!",
        "tip":     "Drink a glass of water right now.",
    }


def chat_with_buddy(
    system_prompt:    str,
    user_message:     str,
    history:          list[dict],
) -> str:
    """
    Multi-turn chat with the Fitness Buddy agent.

    Args:
        system_prompt : Complete system prompt from build_system_prompt()
        user_message  : Latest user message
        history       : Previous messages as list of {"role": ..., "content": ...}

    Returns:
        The AI's response text.
    """
    project_id = os.getenv("WATSONX_PROJECT_ID", "").strip()
    model_id   = os.getenv("GRANITE_MODEL_ID", "ibm/granite-3-3-8b-instruct").strip()

    if not project_id:
        raise RuntimeError("WATSONX_PROJECT_ID is not set.")

    client = _get_client()

    try:
        from ibm_watsonx_ai.foundation_models import ModelInference
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as Params
    except ImportError as e:
        raise RuntimeError("ibm-watsonx-ai not installed.") from e

    # Build full message list: system + history + new user message
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history[-10:])   # keep last 10 turns to avoid context overflow
    messages.append({"role": "user", "content": user_message})

    gen_params = {
        Params.MAX_NEW_TOKENS:     512,
        Params.TEMPERATURE:        0.75,
        Params.REPETITION_PENALTY: 1.05,
    }

    model = ModelInference(
        model_id=model_id,
        credentials=client.credentials,
        project_id=project_id,
        params=gen_params,
    )

    response = model.chat(messages=messages)

    try:
        return response["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as e:
        logger.error("Unexpected chat response: %s", response)
        raise RuntimeError(f"Model response parsing failed: {e}") from e
