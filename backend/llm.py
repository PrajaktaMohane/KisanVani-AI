import time
import logging
import re
from typing import List, Dict, Any, Optional
from backend.config import settings
from backend.language import (
    get_language_name,
    get_no_evidence_message,
    translate_to_target_language,
    is_text_in_target_language
)

logger = logging.getLogger(__name__)

STRICT_UNIFIED_SYSTEM_PROMPT = """You are a trusted multilingual agricultural advisory assistant for Indian farmers.

Your Core Directive:
Answer the farmer's question using ONLY the retrieved agricultural knowledge base context provided below.

CRITICAL LANGUAGE REQUIREMENT:
You MUST output the ENTIRE answer strictly in {target_language}.
Even if the retrieved reference context chunks or documents are written in English, you MUST translate and synthesize the complete explanation into fluent, natural {target_language}.
Do NOT mix English and Marathi/Hindi sentences together.

Grounding & Safety Rules:
1. Do not invent agricultural recommendations or chemicals.
2. Do not use unsupported general knowledge.
3. Do not make assumptions or dosage guesses that are not supported by the retrieved context.
4. If the retrieved context is insufficient, irrelevant, or does not contain a reliable answer, return EXACTLY:
   - For English: "Sorry, verified information for this question was not found in the current agricultural knowledge base."
   - For Hindi: "क्षमा करें, इस प्रश्न के लिए वर्तमान कृषि ज्ञान आधार में सत्यापित जानकारी नहीं मिली।"
   - For Marathi: "क्षमस्व, या प्रश्नासाठी सध्याच्या कृषी ज्ञान आधारामध्ये खात्रीशीर माहिती सापडली नाही."
5. Keep the explanation concise, practical, and easy for a farmer to understand.
6. Keep chemical names, crop names, measurements, and numerical doses accurate.
"""

UNIFIED_USER_PROMPT_TEMPLATE = """Retrieved Verified Agricultural Knowledge Base Evidence:
---
{retrieved_context}
---

Farmer's Question:
"{question}"

Target Response Language: {target_language} (Mandatory: 100% {target_language})
Evidence Confidence: {confidence}

Instructions:
Synthesize a grounded, accurate agricultural answer strictly based on the retrieved evidence above entirely in {target_language}.
Translate all English advisory points into natural {target_language}.
"""

_gemini_client = None
_gemini_cooldown_until = 0.0

def get_gemini_client():
    """Initializes Google GenAI client once."""
    global _gemini_client
    if _gemini_client is None:
        api_key = settings.LLM_API_KEY or settings.GEMINI_API_KEY
        if api_key and len(api_key) > 5:
            try:
                # Try google-genai SDK first
                from google import genai
                _gemini_client = genai.Client(api_key=api_key)
                logger.info(f"Google GenAI Client initialized for model {settings.LLM_MODEL}")
            except Exception as e:
                logger.warning(f"Could not initialize modern google.genai client ({e}), falling back to google.generativeai...")
                try:
                    import google.generativeai as legacy_genai
                    legacy_genai.configure(api_key=api_key)
                    _gemini_client = legacy_genai
                except Exception as l_err:
                    logger.warning(f"Legacy Gemini configure notice: {l_err}")
    return _gemini_client

def generate_grounded_answer(
    question: str,
    retrieved_records: List[Dict[str, Any]],
    context_str: str,
    language_code: str = "en",
    confidence: str = "High",
    is_grounded: bool = True
) -> str:
    """
    Generates a strictly grounded agricultural answer in the user's selected language (mr, hi, or en).
    Ensures 100% language alignment with intelligent 429 quota handling and multi-source fallback.
    """
    global _gemini_cooldown_until
    lang_code = language_code if language_code in ["mr", "hi", "en"] else "mr"

    if not is_grounded or not retrieved_records:
        return get_no_evidence_message(lang_code)

    api_key = settings.LLM_API_KEY or settings.GEMINI_API_KEY
    target_lang_name = get_language_name(lang_code)

    # 1. Try Gemini generation if API key exists and NOT currently in 429 cooldown
    now = time.time()
    if api_key and len(api_key) > 5 and now >= _gemini_cooldown_until:
        client = get_gemini_client()
        if client is not None:
            try:
                system_instruction = STRICT_UNIFIED_SYSTEM_PROMPT.format(target_language=target_lang_name)
                prompt = UNIFIED_USER_PROMPT_TEMPLATE.format(
                    retrieved_context=context_str,
                    question=question,
                    target_language=target_lang_name,
                    confidence=confidence
                )

                generated_text = None
                # Check if it's the modern google.genai.Client
                if hasattr(client, "models"):
                    from google.genai import types
                    resp = client.models.generate_content(
                        model=settings.LLM_MODEL,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            temperature=0.1,
                            max_output_tokens=500
                        )
                    )
                    if resp and resp.text:
                        generated_text = resp.text.strip()
                elif hasattr(client, "GenerativeModel"):
                    model = client.GenerativeModel(
                        model_name=settings.LLM_MODEL,
                        system_instruction=system_instruction,
                        generation_config={
                            "temperature": 0.1,
                            "top_p": 0.8,
                            "max_output_tokens": 500,
                        }
                    )
                    resp = model.generate_content(prompt)
                    if resp and resp.text:
                        generated_text = resp.text.strip()

                if generated_text:
                    if is_text_in_target_language(generated_text, lang_code):
                        return generated_text
                    else:
                        return translate_to_target_language(generated_text, lang_code)

            except Exception as e:
                err_str = str(e)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
                    _gemini_cooldown_until = time.time() + 60.0
                    logger.warning("Gemini 429 Quota Exceeded (Free Tier limit reached). Cooling down for 60s and using deterministic multi-source translation fallback.")
                else:
                    logger.warning(f"Gemini generation notice: {e}. Using deterministic multi-source translation fallback.")

    # 2. Deterministic Extractive Translation Synthesizer (Fast, reliable, zero-quota)
    best_record = retrieved_records[0]
    best_answer = best_record.get("answer", "")

    # Strip any internal source markers
    clean_raw_text = re.sub(r"\[SOURCE \d+:[^\]]+\]:\s*", "", best_answer)
    clean_raw_text = re.sub(r"[*#_`]", "", clean_raw_text).strip()

    # Translate complete text to selected target language by meaning
    translated_answer = translate_to_target_language(clean_raw_text, lang_code)
    return translated_answer
