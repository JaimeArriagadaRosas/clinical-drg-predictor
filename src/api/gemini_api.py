#!/usr/bin/env python3
"""
Gemini API Client for GRD Prediction Chatbot using google-generativeai
"""

import os
import logging
from typing import Optional, List, Dict, Any, Generator
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core.exceptions import RetryError, ResourceExhausted

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiClient:
    """Client for Google Gemini API."""

    def __init__(self, api_key: str = None, model: str = None, system_instruction: str = None, tools: list = None):
        try:
            from dotenv import load_dotenv
            import pathlib
            env_path = pathlib.Path(__file__).parent.parent.parent / '.env'
            if env_path.exists():
                load_dotenv(str(env_path))
        except Exception:
            pass
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY') or ''
        self.model_name = model or os.environ.get('GEMINI_MODEL', 'gemini-1.5-flash')
        self.available = bool(self.api_key)
        logger.info(f"Gemini init - api_key: {'SET' if self.api_key else 'EMPTY'}, model: {self.model_name}")
        if not self.available:
            logger.warning("GEMINI_API_KEY no configurada. Gemini no disponible (modo fallback).")
            return
        genai.configure(api_key=self.api_key)
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        self.generation_config = genai.types.GenerationConfig(
            temperature=float(os.environ.get('TEMPERATURE', 0.7)),
            max_output_tokens=int(os.environ.get('MAX_TOKENS', 1024)),
        )
        kwargs = {
            "model_name": self.model_name,
            "generation_config": self.generation_config,
            "safety_settings": self.safety_settings,
        }
        if system_instruction:
            kwargs["system_instruction"] = system_instruction
        if tools:
            kwargs["tools"] = tools
        self.model = genai.GenerativeModel(**kwargs)

    def generate_content(self, prompt: str, stream: bool = False) -> Any:
        if not self.available:
            return f"[Gemini no disponible] {prompt[:200]}"
        import time
        max_retries = 5
        retry_delay = 5
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt, stream=stream)
                if stream:
                    return response
                return response.text
            except ResourceExhausted as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Rate limited. Retrying in {retry_delay} seconds (attempt {attempt+1}/{max_retries})...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.warning(f"Rate limited permanently: {e}")
                    return "Error: Demasiadas peticiones. Por favor, espera un momento."
            except Exception as e:
                logger.error(f"Gemini API error: {e}")
                return f"Error generando respuesta: {str(e)[:100]}"
        return "Error: Demasiadas peticiones."

    def _validate_history(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        formatted_history = []
        expected_role = 'user'
        for msg in messages:
            role = msg.get('role', 'user')
            if role in ['assistant', 'bot', 'model']:
                role = 'model'
            else:
                role = 'user'
            if formatted_history and formatted_history[-1]['role'] == role:
                formatted_history[-1]['parts'].append(msg.get('content', ''))
            else:
                if formatted_history and expected_role != role:
                    logger.warning(f"Chat history role mismatch. Expected {expected_role}, got {role}.")
                formatted_history.append({'role': role, 'parts': [msg.get('content', '')]})
            expected_role = 'model' if role == 'user' else 'user'
        return formatted_history

    def chat(self, messages: List[Dict[str, str]], stream: bool = False) -> Any:
        if not self.available:
            last_msg = messages[-1].get('content', '') if messages else ''
            return f"[Gemini no disponible] {last_msg[:200]}"
        try:
            if not messages:
                return ""
            history = self._validate_history(messages[:-1])
            last_msg = messages[-1].get('content', '')
            chat_session = self.model.start_chat(history=history)
            import time
            max_retries = 5
            retry_delay = 5
            for attempt in range(max_retries):
                try:
                    response = chat_session.send_message(last_msg, stream=stream)
                    if stream:
                        return response
                    return response.text
                except ResourceExhausted as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limited in chat. Retrying in {retry_delay} seconds (attempt {attempt+1}/{max_retries})...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        logger.warning(f"Rate limited permanently in chat: {e}")
                        return "Error: Demasiadas peticiones. Por favor, espera un momento."
                except Exception as e:
                    logger.error(f"Gemini chat error: {e}")
                    return f"Error: {str(e)[:100]}"
        except Exception as e:
            logger.error(f"Gemini chat initialization error: {e}")
            return f"Error: {str(e)[:100]}"

def create_client(system_instruction: str = None, tools: list = None) -> GeminiClient:
    return GeminiClient(system_instruction=system_instruction, tools=tools)
