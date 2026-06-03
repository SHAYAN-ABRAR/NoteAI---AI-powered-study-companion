import base64
import io
import os

import requests
import streamlit as st
from dotenv import load_dotenv
from PIL import Image


load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llava")
try:
    OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "120"))
except ValueError:
    OLLAMA_TIMEOUT = 120
try:
    OLLAMA_IMAGE_MAX_SIZE = int(os.getenv("OLLAMA_IMAGE_MAX_SIZE", "1280"))
except ValueError:
    OLLAMA_IMAGE_MAX_SIZE = 1280


def image_to_base64(image):
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


def summarize_images(images):
    prompt = """Summarize the pictures in note format in max 100 words.
Use markdown to separate sections clearly."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "images": [image_to_base64(image) for image in images],
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 300,
        },
    }

    response = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json=payload,
        timeout=OLLAMA_TIMEOUT,
    )
    response.raise_for_status()
    return response.json().get("response", "").strip()


images = st.file_uploader(
    "Upload the photos of your note",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
)

if images:
    pil_images = [Image.open(img) for img in images]

    with st.spinner(f"Generating with Ollama model: {OLLAMA_MODEL}"):
        try:
            st.markdown(summarize_images(pil_images))
        except Exception as exc:
            st.error(f"Error calling Ollama: {exc}")
