import logging
from typing import Optional
import google.generativeai as genai
from app.core.config import settings
from app.core.prompts import KISAN_MITRA_SYSTEM_PROMPT, GROUNDED_RAG_USER_PROMPT_TEMPLATE
from app.core.exceptions import LLMGenerationException

logger = logging.getLogger(__name__)

# Mapping ISO code to human language name for LLM prompting
LANGUAGE_NAMES = {
    "hi": "Hindi (हिन्दी)",
    "mr": "Marathi (मराठी)",
    "te": "Telugu (తెలుగు)",
    "ta": "Tamil (தமிழ்)",
    "bn": "Bengali (বাংলা)",
    "gu": "Gujarati (ગુજરાતી)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "pa": "Punjabi (ਪੰਜਾਬੀ)",
    "en": "English"
}

class LLMService:
    _configured: bool = False

    @classmethod
    def _initialize_client(cls):
        if not cls._configured:
            if settings.GEMINI_API_KEY:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                cls._configured = True
            else:
                logger.warning("GEMINI_API_KEY is not set. Real LLM inference requires a valid key.")

    @classmethod
    async def generate_agricultural_advisory(
        cls,
        farmer_query: str,
        retrieved_context: str,
        detected_language: str = "hi",
        is_grounded: bool = True,
        farmer_state: str = "Maharashtra",
        farmer_district: str = "Unspecified",
        crop_name: str = "General Crop",
        soil_type: str = "Standard Soil",
        land_size_acres: float = 2.0
    ) -> str:
        """
        Generates grounded, safe agricultural advice using Google Gemini API.
        """
        cls._initialize_client()

        if not settings.GEMINI_API_KEY:
            # Informative fallback if API key is not yet set by user
            lang_msg = {
                "mr": "कृपया .env फाईलमध्ये तुमचा GEMINI_API_KEY सेट करा. सध्या सिस्टीम स्थानिक RAG मोडमध्ये कार्यरत आहे.",
                "hi": "कृपया .env फ़ाइल में अपना GEMINI_API_KEY सेट करें। वर्तमान में सिस्टम स्थानीय RAG मोड में कार्यरत है।",
                "en": "Please configure your GEMINI_API_KEY in the .env file. Running in local RAG inspection mode."
            }
            return f"{lang_msg.get(detected_language, lang_msg['en'])}\n\n[Retrieved ICAR/KVK Evidence]:\n{retrieved_context[:400]}..."

        lang_name = LANGUAGE_NAMES.get(detected_language, f"{detected_language} language")
        grounded_status = "GROUNDED (Use provided evidence strictly)" if is_grounded else "UNGROUNDED (No verified records matched; enforce safety refusal)"

        formatted_user_prompt = GROUNDED_RAG_USER_PROMPT_TEMPLATE.format(
            farmer_state=farmer_state,
            farmer_district=farmer_district or "Not specified",
            crop_name=crop_name or "Not specified",
            soil_type=soil_type or "Not specified",
            land_size_acres=land_size_acres or 2.0,
            retrieved_context=retrieved_context,
            farmer_query=farmer_query,
            detected_language=lang_name,
            grounded_status=grounded_status
        )

        try:
            model = genai.GenerativeModel(
                model_name=settings.GEMINI_MODEL_NAME,
                system_instruction=KISAN_MITRA_SYSTEM_PROMPT,
                generation_config={
                    "temperature": 0.2,  # Low temperature for deterministic, factual grounding
                    "top_p": 0.8,
                    "max_output_tokens": 800,
                }
            )

            response = model.generate_content(formatted_user_prompt)
            return response.text.strip()

        except Exception as e:
            logger.error(f"Gemini LLM generation failed: {e}")
            raise LLMGenerationException(detail=f"Failed to generate agricultural advice: {str(e)}")
