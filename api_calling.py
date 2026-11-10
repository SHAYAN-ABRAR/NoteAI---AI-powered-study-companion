from dotenv import load_dotenv
import base64
import os, io
from urllib.parse import urlparse
from gtts import gTTS
import streamlit as st
import re
import json
import requests
from PIL import Image

import offline_mode

# ============== ENVIRONMENT SETUP ==============
load_dotenv()

OLLAMA_CLOUD_URL = "https://ollama.com"
DEFAULT_CLOUD_MODEL = "gemma4:31b"


def _setting(name, default=""):
    """Read a setting from Streamlit secrets (hosted apps) or the environment / .env."""
    try:
        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:  # no secrets file: local runs use .env / environment variables
        pass
    return os.getenv(name, default).strip()


def _host_setting():
    host = _setting("OLLAMA_BASE_URL")
    if host:
        return host
    # OLLAMA_HOST is also the Ollama daemon's own bind setting (e.g. "0.0.0.0"),
    # so only use it here when it is a full URL.
    host = _setting("OLLAMA_HOST")
    return host if host.startswith(("http://", "https://")) else ""


# With an API key the app talks to Ollama Cloud (or OLLAMA_BASE_URL, if set);
# without one it uses a local Ollama server, and offline mode if none is running.
OLLAMA_API_KEY = _setting("OLLAMA_API_KEY")
OLLAMA_BASE_URL = (_host_setting() or (OLLAMA_CLOUD_URL if OLLAMA_API_KEY else "http://localhost:11434")).rstrip("/")


def _is_ollama_cloud(url=None):
    host = urlparse(url or OLLAMA_BASE_URL).hostname or ""
    return host == "ollama.com" or host.endswith(".ollama.com")


def normalize_model_name(model):
    """ollama.com names cloud models without the local '-cloud' suffix (gemma4:31b-cloud -> gemma4:31b)."""
    model = (model or "").strip()
    if _is_ollama_cloud() and model.endswith("-cloud"):
        model = model[: -len("-cloud")]
    return model


OLLAMA_MODEL = normalize_model_name(_setting("OLLAMA_MODEL") or (DEFAULT_CLOUD_MODEL if OLLAMA_API_KEY else "llava"))


def _auth_headers():
    return {"Authorization": f"Bearer {OLLAMA_API_KEY}"} if OLLAMA_API_KEY else {}


try:
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))
except ValueError:
    OLLAMA_TIMEOUT = 120

try:
    OLLAMA_IMAGE_MAX_SIZE = int(os.getenv("OLLAMA_IMAGE_MAX_SIZE", "1280"))
except ValueError:
    OLLAMA_IMAGE_MAX_SIZE = 1280

try:
    OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "700"))
except ValueError:
    OLLAMA_NUM_PREDICT = 700


def _image_to_base64(image):
    """
    Convert a PIL image to base64 for Ollama's vision API.
    """
    image_to_save = image.copy()

    if OLLAMA_IMAGE_MAX_SIZE > 0:
        image_to_save.thumbnail(
            (OLLAMA_IMAGE_MAX_SIZE, OLLAMA_IMAGE_MAX_SIZE),
            Image.Resampling.LANCZOS,
        )

    if image_to_save.mode in ("RGBA", "LA"):
        background = Image.new("RGB", image_to_save.size, "white")
        alpha = image_to_save.getchannel("A")
        background.paste(image_to_save, mask=alpha)
        image_to_save = background
    elif image_to_save.mode != "RGB":
        image_to_save = image_to_save.convert("RGB")

    buffer = io.BytesIO()
    image_to_save.save(buffer, format="JPEG", quality=85, optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


@st.cache_data(ttl=30, show_spinner=False)
def _probe_ollama(base_url, use_key):
    """
    Return (reachable, model names, error) for the configured Ollama server.
    Cached for 30s so widget interactions don't trigger a network call on every rerun.
    """
    try:
        response = requests.get(
            f"{base_url}/api/tags",
            headers=_auth_headers() if use_key else {},
            timeout=6 if use_key else 3,
        )
        response.raise_for_status()
        models = response.json().get("models", [])
        return True, [model["name"] for model in models if model.get("name")], None
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "error"
        return False, [], f"HTTP {status}"
    except requests.exceptions.RequestException as exc:
        return False, [], type(exc).__name__
    except ValueError:
        return False, [], "invalid response"


def get_ollama_models():
    """
    Return the model names on the configured Ollama server (local, or Ollama Cloud
    when OLLAMA_API_KEY is set), or an empty list if it can't be reached.
    """
    return _probe_ollama(OLLAMA_BASE_URL, bool(OLLAMA_API_KEY))[1]


def get_ai_status():
    """
    Which AI path the app is using:
      "cloud"   - OLLAMA_API_KEY is set and the server answered
      "local"   - a local (or self-hosted) Ollama server answered
      "offline" - no model reachable; offline_mode reads the photos on-device
    """
    reachable, models, error = _probe_ollama(OLLAMA_BASE_URL, bool(OLLAMA_API_KEY))
    if reachable:
        mode = "cloud" if OLLAMA_API_KEY else "local"
    else:
        mode = "offline"
    return {
        "mode": mode,
        "key_configured": bool(OLLAMA_API_KEY),
        "is_ollama_cloud": _is_ollama_cloud(),
        "host": OLLAMA_BASE_URL,
        "models": models,
        "error": error,
        "ocr": offline_mode.ocr_available(),
    }


def _ollama_generate(prompt, images=None, response_format=None, model=None, num_predict=None):
    """
    Generate text with the configured Ollama model (local server or Ollama Cloud).
    Uses /api/chat, which both a local Ollama server and ollama.com support.
    """
    active_model = normalize_model_name(model or OLLAMA_MODEL)
    message = {"role": "user", "content": prompt}

    if images:
        message["images"] = [_image_to_base64(image) for image in images]

    payload = {
        "model": active_model,
        "messages": [message],
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": num_predict or OLLAMA_NUM_PREDICT,
        },
    }

    if response_format:
        payload["format"] = response_format

    where = "Ollama Cloud" if _is_ollama_cloud() else f"Ollama at {OLLAMA_BASE_URL}"

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            headers=_auth_headers(),
            timeout=OLLAMA_TIMEOUT,
        )
        response.raise_for_status()
        content = (response.json().get("message") or {}).get("content", "").strip()
    except requests.exceptions.ConnectionError as exc:
        hint = ("Check the internet connection." if OLLAMA_API_KEY
                else "Start Ollama and make sure a vision-capable model is installed.")
        raise RuntimeError(f"Could not connect to {where}. {hint}") from exc
    except requests.exceptions.Timeout as exc:
        raise RuntimeError(
            f"{where} timed out after {OLLAMA_TIMEOUT} seconds. "
            "Try a smaller image, a faster model, or increase OLLAMA_TIMEOUT."
        ) from exc
    except requests.exceptions.HTTPError as exc:
        try:
            detail = response.json().get("error") or response.text.strip()
        except ValueError:
            detail = response.text.strip() if response.text else str(exc)

        if response.status_code in (401, 403):
            detail = f"{where} rejected the request (HTTP {response.status_code}). Check OLLAMA_API_KEY."
        elif "not found" in detail.lower() and active_model in detail:
            if OLLAMA_API_KEY:
                detail = f"Model '{active_model}' isn't available on {where}. Select another model from the sidebar."
            else:
                detail = (
                    f"Model '{active_model}' is not installed in Ollama. "
                    f"Run 'ollama pull {active_model}' or select an installed model from the sidebar."
                )

        raise RuntimeError(f"Ollama request failed: {detail}") from exc
    except ValueError as exc:
        raise RuntimeError("Ollama returned an invalid JSON response.") from exc

    if not content:
        raise RuntimeError("The model returned an empty response.")
    return content


def _use_ai():
    return get_ai_status()["mode"] != "offline"


def _fallback_notice(what, error):
    st.warning(
        f"⚠️ Couldn't create the {what} with the AI model: {error} "
        "Showing offline results built from the text in your photos instead."
    )


def _offline_result(result, language):
    if result is None:
        st.warning(f"📴 {offline_mode.unreadable_message(language)}")
    return result

# ============== NOTE GENERATOR ==============
def note_generator(images, language="Bengali", model=None):
    """
    Generate comprehensive notes from images
    """
    if language == "Bengali":
        prompt = """Summarize the pictures in detailed note format in Bengali language (max 300 words).
        Structure your response with:
        1. **মূল বিষয়** (Main Topic)
        2. **মূল ধারণা** (Key Concepts) 
        3. **গুরুত্বপূর্ণ পয়েন্ট** (Important Points)
        4. **সংক্ষিপ্ত সারসংক্ষেপ** (Summary)

        Use markdown for clarity and proper formatting.
        Use **bold text** for section titles. Do not use '#' heading syntax."""
    else:  # English
        prompt = """Summarize the pictures in detailed note format in English language (max 300 words).
        Structure your response with:
        1. **Main Topic**
        2. **Key Concepts** 
        3. **Important Points**
        4. **Summary**

        Use markdown for clarity and proper formatting.
        Use **bold text** for section titles. Do not use '#' heading syntax."""
    
    if _use_ai():
        try:
            return _ollama_generate(prompt, images, model=model, num_predict=500)
        except Exception as e:
            _fallback_notice("notes", e)
    return _offline_result(offline_mode.notes(images, language), language)

# ============== AUDIO TRANSCRIPTION ==============
def audio_transcription(text, language="Bengali"):
    """
    Convert text to audio in selected language using Google Text-to-Speech
    """
    try:
        lang_code = 'bn' if language == "Bengali" else 'en'
        speech = gTTS(text, lang=lang_code, slow=False, tld='co.in')
        audio_buffer = io.BytesIO()
        speech.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer
    except Exception as e:
        st.error(f"❌ Error generating audio: {str(e)}")
        return None

# ============== QUIZ GENERATOR ==============
def quiz_generator(images, difficulty, language="Bengali", model=None):
    """
    Generate 5 multiple-choice questions and return structured JSON (reliable parsing)
    """
    difficulty_map_bn = {
        "Easy": "সহজ (Easy) - মৌলিক ধারণা এবং সংজ্ঞা",
        "Medium": "মাঝারি (Medium) - ধারণার প্রয়োগ",
        "Hard": "কঠিন (Hard) - জটিল বিশ্লেষণ এবং সংশ্লেষণ"
    }
    difficulty_map_en = {
        "Easy": "Easy - Basic concepts and definitions",
        "Medium": "Medium - Application of concepts",
        "Hard": "Hard - Complex analysis and synthesis"
    }
    
    difficulty_desc = difficulty_map_bn.get(difficulty, "Medium") if language == "Bengali" else difficulty_map_en.get(difficulty, "Medium")
    
    if language == "Bengali":
        prompt = f"""Generate 5 multiple-choice questions based on the images with {difficulty_desc} difficulty level in Bengali.
Return ONLY valid JSON. No extra text, no markdown.

Format exactly:
{{
  "questions": [
    {{
      "question": "প্রশ্ন এখানে লিখুন",
      "options": {{
        "A": "অপশন A",
        "B": "অপশন B",
        "C": "অপশন C",
        "D": "অপশন D"
      }},
      "correct_answer": "B",
      "explanation": "2-3 লাইনের বিস্তারিত ব্যাখ্যা কেন এটি সঠিক।"
    }}
  ]
}}
Make questions clear, options plausible, and explanations educational."""
    else:  # English
        prompt = f"""Generate 5 multiple-choice questions based on the images with {difficulty_desc} difficulty level in English.
Return ONLY valid JSON. No extra text, no markdown.

Format exactly:
{{
  "questions": [
    {{
      "question": "Question text here",
      "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      }},
      "correct_answer": "B",
      "explanation": "2-3 lines detailed explanation why this is correct."
    }}
  ]
}}
Make questions clear, options plausible, and explanations educational."""

    if _use_ai():
        try:
            return _ollama_generate(prompt, images, response_format="json", model=model, num_predict=1100)
        except Exception as e:
            _fallback_notice("quiz", e)
    return _offline_result(offline_mode.quiz(images, difficulty, language), language)

# ============== ADDITIONAL FEATURES ==============

def flashcard_generator(images, language="Bengali", model=None):
    """
    Generate flashcard-style Q&A pairs for quick review
    """
    if language == "Bengali":
        prompt = """Create 5 flashcard pairs in Bengali format from the images.
        Format: 
        **প্রশ্ন (Question):** [Question in Bengali]
        **উত্তর (Answer):** [Answer in Bengali]
        
        Make them concise and perfect for studying."""
    else:
        prompt = """Create 5 flashcard pairs in English format from the images.
        Format: 
        **Question:** [Question in English]
        **Answer:** [Answer in English]
        
        Make them concise and perfect for studying."""
    
    if _use_ai():
        try:
            return _ollama_generate(prompt, images, model=model, num_predict=600)
        except Exception as e:
            _fallback_notice("flashcards", e)
    return _offline_result(offline_mode.flashcards(images, language), language)

def key_points_extractor(images, language="Bengali", model=None):
    """
    Extract key points and bullet points for quick reference
    """
    if language == "Bengali":
        prompt = """Extract the most important key points from the images in Bengali.
        Format as a bullet-point list with:
        - মূল বিষয়গুলি (Main topics)
        - গুরুত্বপূর্ণ সূত্র/সংজ্ঞা (Critical formulas/definitions)
        - গুরুত্বপূর্ণ তথ্য (Important facts)
        
        Keep it concise and organized."""
    else:
        prompt = """Extract the most important key points from the images in English.
        Format as a bullet-point list with:
        - Main topics
        - Critical formulas/definitions
        - Important facts
        
        Keep it concise and organized."""
    
    if _use_ai():
        try:
            return _ollama_generate(prompt, images, model=model, num_predict=500)
        except Exception as e:
            _fallback_notice("key points", e)
    return _offline_result(offline_mode.key_points(images, language), language)

def extract_correct_answers(quiz_content):
    """
    Extract correct answers from quiz content
    """
    # Pattern to find correct answers (works for both Bengali and English)
    patterns = [
        r'[সS]ঠিক [উU]ত্তর.*?:\s*([A-D])\)',
        r'[Cc]orrect [Aa]nswer.*?:\s*([A-D])\)',
        r'[সS]ঠিক [উU]ত্তর.*?:\s*([A-D])',
        r'[Cc]orrect [Aa]nswer.*?:\s*([A-D])',
    ]
    
    answers = []
    for pattern in patterns:
        matches = re.findall(pattern, quiz_content)
        if matches:
            answers.extend(matches)
    
    return answers

def parse_quiz_json(raw_text):
    """
    Safely parse JSON output from Ollama
    """
    if not raw_text:
        return []
    try:
        cleaned = raw_text.strip()
        # Remove possible markdown code blocks
        if cleaned.startswith("```json"):
            cleaned = cleaned.split("```json")[1].split("```")[0].strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1].split("```")[0].strip()
        
        data = json.loads(cleaned)
        return data.get("questions", [])[:5]  # ensure exactly 5 questions
    except Exception as e:
        st.error(f"❌ JSON parsing failed: {str(e)}")
        return []
