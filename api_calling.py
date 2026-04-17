from google import genai
from dotenv import load_dotenv
import os, io
from gtts import gTTS
import streamlit as st
import re
import json

# ============== ENVIRONMENT SETUP ==============
load_dotenv()

my_api_key = os.getenv("GEMINI_API_KEY")

if not my_api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in .env file")

# Initialize client
client = genai.Client(api_key=my_api_key)

# ============== NOTE GENERATOR ==============
def note_generator(images, language="Bengali"):
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
        
        Use markdown for clarity and proper formatting."""
    else:  # English
        prompt = """Summarize the pictures in detailed note format in English language (max 300 words).
        Structure your response with:
        1. **Main Topic**
        2. **Key Concepts** 
        3. **Important Points**
        4. **Summary**
        
        Use markdown for clarity and proper formatting."""
    
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[*images, prompt]
        )
        return response.text
    except Exception as e:
        st.error(f"❌ Error generating notes: {str(e)}")
        return "Unable to generate notes. Please try again."

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
def quiz_generator(images, difficulty, language="Bengali"):
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

    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[*images, prompt]
        )
        return response.text
    except Exception as e:
        st.error(f"❌ Error generating quiz: {str(e)}")
        return None

# ============== ADDITIONAL FEATURES ==============

def flashcard_generator(images, language="Bengali"):
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
    
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[*images, prompt]
        )
        return response.text
    except Exception as e:
        st.error(f"❌ Error generating flashcards: {str(e)}")
        return None

def key_points_extractor(images, language="Bengali"):
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
    
    try:
        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=[*images, prompt]
        )
        return response.text
    except Exception as e:
        st.error(f"❌ Error extracting key points: {str(e)}")
        return None

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
    Safely parse JSON output from Gemini
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