import os
import re
import json
import logging
import urllib.request
import urllib.parse
from typing import Tuple, Optional, Dict, Any

logger = logging.getLogger(__name__)

MARATHI_DISTINCT_WORDS = [
    "आहे", "नाही", "करावे", "करावा", "करावी", "काय", "उपाय", "बोंडअळी", "बोंड",
    "खत", "खते", "पीक", "पिकावर", "पिकासाठी", "पिकाला", "पिकाची", "पिकावरील",
    "गहू", "गव्हाची", "गव्हाला", "गव्हासाठी", "कापूस", "कापसाची", "कापसाला", "कापसावर", "कापसावरील",
    "सोयाबीन", "सोयाबीनची", "सोयाबीनला", "सोयाबीनसाठी", "तांदूळ", "तांदळाची", "तांदळाला", "तांदळावरील",
    "पाणी", "सापळे", "फवारणी", "फुलगळ", "रोग", "कीड", "किडीचे", "कधी", "द्यावे", "लागवड", "पेरणी", "काढणी"
]

HINDI_DISTINCT_WORDS = [
    "है", "नहीं", "करें", "करे", "क्या", "उपाय", "इलाज", "छिड़काव", "रोग",
    "कीट", "खाद", "फसल", "गेहूं", "कपास", "सोयाबीन", "धान", "सिंचाई", "कब", "दवा",
    "बुवाई", "मात्रा", "लक्षण", "रोकथाम", "डालें", "कीटनाशक", "कटाई", "रोपाई", "सुंडी"
]

def detect_language(text: str) -> str:
    """
    Detects whether text is in Marathi ('mr'), Hindi ('hi'), or English ('en').
    """
    if not text:
        return "en"

    text_clean = text.strip()
    words = set(re.findall(r"\b\w+\b", text_clean.lower()))

    # Check for Devanagari Unicode range
    has_devanagari = any("\u0900" <= char <= "\u097F" for char in text_clean)

    if not has_devanagari:
        return "en"

    # Count Marathi vs Hindi marker matches
    marathi_matches = sum(1 for w in words if w in MARATHI_DISTINCT_WORDS or any(w.startswith(mw) for mw in ["सोयाबीन", "कापसा", "गव्हा", "तांदळा", "पिका", "किडी"]))
    hindi_matches = sum(1 for w in words if w in HINDI_DISTINCT_WORDS)

    if marathi_matches > hindi_matches:
        return "mr"
    elif hindi_matches > marathi_matches:
        return "hi"

    if any(m in text_clean for m in ["आहे", "करावे", "करावी", "कापूस", "गहू", "बोंडअळी", "पिका"]):
        return "mr"
    return "hi"

def get_language_name(code: str) -> str:
    """Returns descriptive language name for prompt context."""
    names = {
        "en": "English",
        "hi": "Hindi (हिन्दी)",
        "mr": "Marathi (मराठी)"
    }
    return names.get(code, "English")

def get_language_display_name(code: str) -> str:
    """Returns clean English language name (e.g. Marathi, Hindi, English)."""
    names = {
        "en": "English",
        "hi": "Hindi",
        "mr": "Marathi"
    }
    return names.get(code, "English")

def get_no_evidence_message(lang_code: str) -> str:
    """
    Returns generic localized refusal message when verified evidence is not found in knowledge base.
    """
    messages = {
        "en": "Sorry, verified information for this question was not found in the current agricultural knowledge base.",
        "hi": "क्षमा करें, इस प्रश्न के लिए वर्तमान कृषि ज्ञान आधार में सत्यापित जानकारी नहीं मिली।",
        "mr": "क्षमस्व, या प्रश्नासाठी सध्याच्या कृषी ज्ञान आधारामध्ये खात्रीशीर माहिती सापडली नाही."
    }
    return messages.get(lang_code, messages["en"])

def translate_to_target_language(text: str, target_language_code: str) -> str:
    """
    Translates English/multilingual text into the user's selected language (mr, hi, or en).
    Preserves numbers, measurements, chemical dosages, and technical terms factually.
    """
    if not text:
        return ""

    target_lang = target_language_code if target_language_code in ["mr", "hi", "en"] else "mr"

    # Clean raw markdown and formatting noise before translation
    clean_input = re.sub(r"\[SOURCE \d+:[^\]]+\]:\s*", "", text)
    clean_input = re.sub(r"[*#_`]", "", clean_input).strip()
    if not clean_input:
        return text

    # Check if text is already in the target script/language
    has_devanagari = any("\u0900" <= char <= "\u097F" for char in clean_input)

    if target_lang == "en" and not has_devanagari:
        return clean_input

    if target_lang in ["mr", "hi"] and is_text_in_target_language(clean_input, target_lang):
        return clean_input

    # Translate using Google Translate API with tight 3.5s timeout
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=" + target_lang + "&dt=t&q=" + urllib.parse.quote(clean_input[:1000])
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=3.5) as response:
            result = json.loads(response.read().decode("utf-8"))
            translated = "".join([part[0] for part in result[0] if part and part[0]])
            if translated and len(translated.strip()) > 3:
                return translated.strip()
    except Exception as e:
        logger.warning(f"Translation API call warning for {target_lang}: {e}")

    return clean_input

def normalize_and_translate_query(query: str, language_code: Optional[str] = None) -> str:
    """
    Translates or normalizes Marathi / Hindi queries into an English agricultural search representation.
    """
    lang = language_code or detect_language(query)
    if lang == "en":
        return query

    # Translate the actual query directly to English
    translated = translate_to_target_language(query, "en")
    if translated and translated != query:
        return translated

    return query

def is_text_in_target_language(text: str, target_lang: str) -> bool:
    """
    Validates whether the text matches the requested target language script.
    """
    if not text or len(text.strip()) < 3:
        return True

    devanagari_chars = sum(1 for c in text if "\u0900" <= c <= "\u097F")
    latin_chars = sum(1 for c in text if ("a" <= c <= "z" or "A" <= c <= "Z"))

    if target_lang in ["mr", "hi"]:
        # Should be predominantly Devanagari script
        if devanagari_chars >= 5 and devanagari_chars > latin_chars:
            return True
        return False
    elif target_lang == "en":
        # Should be predominantly Latin script
        if latin_chars > devanagari_chars:
            return True
        return False
    return True

def is_meaningful_transcript(text: str) -> bool:
    """
    Checks whether a transcript is a meaningful question or obvious noise/gibberish.
    """
    if not text or len(text.strip()) < 3:
        return False

    clean = text.strip()
    words = [w for w in re.findall(r"\b\w+\b", clean) if len(w) > 0]
    if len(words) == 0:
        return False

    # Check for excessive repetition of single token (e.g. "a a a a a")
    if len(words) >= 4 and len(set(words)) == 1:
        return False

    # Check if text has at least some alphabetic or Devanagari characters
    letters = sum(1 for c in clean if c.isalpha() or ("\u0900" <= c <= "\u097F"))
    if letters < 3:
        return False

    return True

def get_unintelligible_message(lang_code: str) -> str:
    """
    Returns polite refusal when speech recognition audio could not be clearly understood.
    """
    messages = {
        "mr": "क्षमस्व, मला तुमचा प्रश्न स्पष्टपणे समजला नाही. कृपया पुन्हा एकदा बोला.",
        "hi": "क्षमा करें, मैं आपका प्रश्न स्पष्ट रूप से समझ नहीं पाया। कृपया दोबारा बोलें।",
        "en": "Sorry, I couldn't understand your question clearly. Please try again."
    }
    return messages.get(lang_code, messages["mr"])

