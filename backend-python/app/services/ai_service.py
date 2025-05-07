import requests
import json
import re
import logging
import time
import random
from typing import Dict, List, Union, Optional, Any, Generator

# Configure logging
logger = logging.getLogger(__name__)

# AI Model configuration
AI_MODEL = "qwen3:4b"  # Default model

# Server configuration
OLLAMA_SERVERS = [
    "https://ollama4.kkhost.pl",
]
CURRENT_SERVER = OLLAMA_SERVERS[0]
last_server_switch_time = time.time()

# Server status
ai_server_status = {
    'last_checked': None,
    'is_online': False,
    'ping_time': 0,
    'available_models': [],
    'current_server': CURRENT_SERVER
}

def check_ai_server_health(force_check: bool = False) -> Dict[str, Any]:
    """
    Check AI server status and switch to another if current is unavailable

    Args:
        force_check: Whether to force a check regardless of time since last check

    Returns:
        Dict with server status information
    """
    global CURRENT_SERVER, ai_server_status, last_server_switch_time

    # Only check every 5 minutes unless forced
    current_time = time.time()
    if not force_check and ai_server_status['last_checked'] and current_time - ai_server_status['last_checked'] < 300:
        return ai_server_status

    # Check if current server is working
    try:
        start_time = time.time()
        response = requests.get(f"{CURRENT_SERVER}/api/tags", timeout=3)
        ping_time = time.time() - start_time

        if response.status_code == 200:
            models = response.json().get("models", [])
            available_models = [model.get("name") for model in models]
            ai_server_status = {
                'last_checked': current_time,
                'is_online': True,
                'ping_time': round(ping_time, 3),
                'available_models': available_models,
                'current_server': CURRENT_SERVER
            }
            logger.info(f"AI Server available: {CURRENT_SERVER}, ping: {ping_time:.3f}s")
            return ai_server_status
    except Exception as e:
        logger.warning(f"Main AI server {CURRENT_SERVER} unavailable: {e}")

    # If current server doesn't work, check others
    # But only if at least 30 seconds passed since last switch
    if current_time - last_server_switch_time > 30:
        # Try to find another working server
        viable_servers = [s for s in OLLAMA_SERVERS if s != CURRENT_SERVER]
        random.shuffle(viable_servers) # Check alternatives in random order

        switched = False
        for server_to_try in viable_servers:
            try:
                logger.info(f"Attempting to switch to server: {server_to_try}")
                start_time = time.time()
                response = requests.get(f"{server_to_try}/api/tags", timeout=3)
                ping_time = time.time() - start_time
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    available_models = [model.get("name") for model in models]
                    CURRENT_SERVER = server_to_try
                    last_server_switch_time = current_time
                    ai_server_status = {
                        'last_checked': current_time,
                        'is_online': True,
                        'ping_time': round(ping_time, 3),
                        'available_models': available_models,
                        'current_server': CURRENT_SERVER
                    }
                    logger.info(f"Successfully switched to server: {CURRENT_SERVER}, ping: {ping_time:.3f}s")
                    switched = True
                    return ai_server_status
            except Exception as e_switch:
                logger.warning(f"Alternative server {server_to_try} unavailable: {e_switch}")

        if not switched: # If all alternatives also failed
            ai_server_status['is_online'] = False
            logger.error(f"All AI servers confirmed unavailable after checking alternatives.")

    else: # Still in cooldown from last switch, and current server failed initial check
        ai_server_status['is_online'] = False
        logger.warning(f"Current AI server {CURRENT_SERVER} is offline. In cooldown, not switching yet.")


    if not ai_server_status['is_online']:
         ai_server_status.update({
            'last_checked': current_time,
            'ping_time': 0,
            'available_models': [],
            # Keep current_server as is, so we know which one was last tried
            'error_message': "All AI servers are unavailable!"
        })

    return ai_server_status

def get_ai_response(
    prompt: str,
    system_prompt: Optional[str] = None,
    context: Optional[List[Dict[str, str]]] = None,
    format: Optional[Union[str, Dict[str, Any]]] = None,
    options: Optional[Dict[str, Any]] = None
) -> str:
    """
    Send a request to Ollama API and return the response

    Args:
        prompt: User query
        system_prompt: System instructions for the model
        context: Conversation context
        format: Optional "json" string or a JSON schema dictionary for structured output
        options: Optional dictionary for Ollama options (e.g., temperature)

    Returns:
        Response from the AI model as a string
    """
    server_status = check_ai_server_health()
    if not server_status['is_online']:
        logger.error("get_ai_response called but no AI server is online.")
        return "Przepraszamy, wszyscy asystenci AI są obecnie niedostępni. Prosimy spróbować ponownie za chwilę."

    api_url = f"{CURRENT_SERVER}/api/chat"

    effective_system_prompt = system_prompt if system_prompt else "You are a helpful assistant."
    if "NEVER include <think>" not in effective_system_prompt:
        effective_system_prompt += "\nNEVER include <think> tags in your responses."
    if "Always respond ONLY in Polish" not in effective_system_prompt and "Polish" in effective_system_prompt:
         effective_system_prompt += " Always respond ONLY in Polish."

    messages = [{"role": "system", "content": effective_system_prompt}]
    if context: messages.extend(context)
    messages.append({"role": "user", "content": prompt})

    # Default Ollama options
    payload_options = {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40
    }
    if options:
        payload_options.update(options)

    payload = {
        "model": AI_MODEL,
        "messages": messages,
        "options": payload_options,
        "stream": False
    }

    if format:
        payload["format"] = format

    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Sending request to API: {api_url} (model: {AI_MODEL}, format: {type(format).__name__ if format else 'None'}, attempt {attempt+1}/{max_retries+1})")
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

            response = requests.post(api_url, json=payload, timeout=90)

            if response.status_code == 200:
                try:
                    result = response.json()
                    content = result.get("message", {}).get("content")
                    if content is None:
                        logger.error(f"Ollama API success (200) but no 'content' in message. Full response: {result}")
                        return "Przepraszamy, asystent AI zwrócił niekompletną odpowiedź."

                    if len(content) < 50:
                        logger.info(f"Short response from AI: '{content}'")

                    return re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
                except json.JSONDecodeError as e_json_decode:
                    logger.error(f"Ollama API success (200) but failed to decode JSON response: {e_json_decode}. Response text: {response.text[:500]}")
                    if attempt < max_retries:
                        logger.info("Retrying due to JSON decode error on successful status...")
                        check_ai_server_health(force_check=True)
                        api_url = f"{CURRENT_SERVER}/api/chat"
                        continue
                    return "Przepraszamy, asystent AI zwrócił odpowiedź w nieoczekiwanym formacie."

            else:
                logger.error(f"Ollama API error: {response.status_code}, Response: {response.text[:500]}")
                if attempt < max_retries:
                    check_ai_server_health(force_check=True)
                    api_url = f"{CURRENT_SERVER}/api/chat"
                    logger.info(f"Retrying with server: {CURRENT_SERVER} after HTTP error.")
                    continue
                return f"Przepraszamy, wystąpił błąd komunikacji z asystentem AI (kod {response.status_code})."

        except requests.exceptions.Timeout:
            logger.error(f"Timeout (90s) during Ollama API communication (attempt {attempt+1})")
            if attempt < max_retries:
                check_ai_server_health(force_check=True)
                api_url = f"{CURRENT_SERVER}/api/chat"
                logger.info(f"Retrying with server: {CURRENT_SERVER} after timeout.")
                continue
            return "Przepraszamy, upłynął limit czasu oczekiwania na odpowiedź od asystenta AI."

        except Exception as e:
            logger.error(f"Generic exception during Ollama API call (attempt {attempt+1}): {e}", exc_info=True)
            if attempt < max_retries:
                check_ai_server_health(force_check=True)
                api_url = f"{CURRENT_SERVER}/api/chat"
                logger.info(f"Retrying with server: {CURRENT_SERVER} after generic exception.")
                continue
            return f"Przepraszamy, wystąpił nieoczekiwany błąd: {str(e)}."

    return "Nie udało się uzyskać odpowiedzi od asystenta AI po wielu próbach."

def get_structured_output(
    prompt: str,
    system_prompt: str,
    schema: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Get structured JSON output from the AI model using Ollama's format parameter.

    Args:
        prompt: User query
        system_prompt: System instructions for the model (should guide towards JSON output)
        schema: The JSON schema dictionary to pass to Ollama's 'format' parameter.

    Returns:
        Parsed JSON data as a dictionary, or an error dictionary if parsing fails.
    """
    system_prompt_for_json = f"{system_prompt}\n\nYour response MUST be a single, valid JSON object that strictly adheres to the provided schema. Do not add any explanatory text before or after the JSON object."

    ollama_options = {"temperature": 0.0}

    raw_response_content = get_ai_response(
        prompt,
        system_prompt_for_json,
        format=schema,
        options=ollama_options
    )

    error_response_template = {
        "error": "Failed to get valid structured output",
        "details": "",
        "raw_response": raw_response_content,
        "job_matches": [],
        "extracted_user_skills": []
    }

    if not raw_response_content:
        logger.error("get_structured_output: Received empty content from get_ai_response.")
        error_response_template["details"] = "Received empty content from AI service"
        return error_response_template

    if raw_response_content.startswith("Przepraszamy") or raw_response_content.startswith("Nie udało się"):
        logger.error(f"get_structured_output: AI service returned a user-facing error message: {raw_response_content}")
        error_response_template["details"] = "AI service returned a non-JSON error message"
        return error_response_template

    try:
        parsed_json = json.loads(raw_response_content)
        logger.info("Successfully parsed structured JSON output from AI.")
        return parsed_json

    except json.JSONDecodeError as e_direct_parse:
        logger.warning(f"Failed to directly parse AI response as JSON (expected with Ollama's schema format): {e_direct_parse}. Raw content snippet: '{raw_response_content[:500]}...'")

        match = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", raw_response_content)
        if match:
            json_str = match.group(1)
            logger.info("Found a ```json``` block, attempting to parse it as fallback.")
            try:
                parsed_json_fallback = json.loads(json_str)
                logger.info("Successfully parsed JSON from ```json``` block (fallback).")
                return parsed_json_fallback
            except json.JSONDecodeError as e_block_parse:
                logger.error(f"Failed to parse JSON from ```json``` block (fallback): {e_block_parse}. Block: '{json_str[:500]}...'")
                error_response_template["error"] = "Failed to parse JSON from extracted block"
                error_response_template["details"] = str(e_block_parse)
                return error_response_template

        logger.error(f"All attempts to parse structured output failed. Final error on direct parse: {e_direct_parse}.")
        error_response_template["details"] = str(e_direct_parse)
        return error_response_template

    except Exception as e_general:
        logger.error(f"General unexpected error during structured output processing: {e_general}. Raw content: '{raw_response_content[:1000]}...'", exc_info=True)
        error_response_template["error"] = "Unexpected error processing structured AI response"
        error_response_template["details"] = str(e_general)
        return error_response_template