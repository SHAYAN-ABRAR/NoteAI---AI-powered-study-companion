import streamlit as st
from api_calling import OLLAMA_MODEL, get_ollama_models, note_generator, audio_transcription, quiz_generator, flashcard_generator, key_points_extractor, extract_correct_answers, parse_quiz_json
from PIL import Image
import re

# ============== PAGE CONFIGURATION ==============
st.set_page_config(
    page_title="📚 AI Quiz & Note Master",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============== CUSTOM CSS — LUXURY DARK GLASSMORPHISM ==============
st.markdown("""
    <style>
    /* Luxury geometric display face + clean body sans + mono for UI labels */
    @import url('https://api.fontshare.com/v2/css?f[]=clash-display@500,600,700&f[]=satoshi@400,500,700&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --font-display: 'Clash Display', 'Satoshi', system-ui, sans-serif;
        --font-body: 'Satoshi', system-ui, -apple-system, sans-serif;
        --font-mono: 'JetBrains Mono', 'Cascadia Code', monospace;

        /* Core glassmorphism stack */
        --glass-fill: rgba(17, 24, 39, 0.45);
        --glass-border: rgba(255, 255, 255, 0.08);
        --glass-border-hover: rgba(255, 255, 255, 0.18);
        --ease-premium: cubic-bezier(0.16, 1, 0.3, 1);
        /* Layered depth: soft expansive glow + tight sharp shadow + inner glass edge */
        --shadow-glass: 0 30px 60px -15px rgba(0, 0, 0, 0.6),
                        0 2px 6px rgba(0, 0, 0, 0.35),
                        inset 0 1px 0 rgba(255, 255, 255, 0.06);
        --shadow-glass-hover: 0 40px 80px -20px rgba(0, 0, 0, 0.7),
                              0 4px 12px rgba(0, 0, 0, 0.4),
                              0 0 40px -10px rgba(139, 92, 246, 0.25),
                              inset 0 1px 0 rgba(255, 255, 255, 0.10);

        --text-primary: rgba(255, 255, 255, 0.95);
        --text-secondary: rgba(156, 163, 175, 0.8);
    }

    /* ===== AMBIENT STAGE: matte deep charcoal + glowing orbs + noise grain =====
       Orbs are fixed to the viewport while content scrolls, so glass panels
       dynamically tint and distort them as they pass over. Noise is the top
       background layer (subtle film grain). */
    .stApp {
        background-color: #07090F;
        background-image:
            url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%25' height='100%25' filter='url(%23n)' opacity='0.05'/></svg>"),
            radial-gradient(38% 32% at 10% 6%, rgba(124, 58, 237, 0.34) 0%, transparent 65%),
            radial-gradient(30% 26% at 92% 10%, rgba(34, 211, 238, 0.20) 0%, transparent 65%),
            radial-gradient(42% 38% at 78% 88%, rgba(236, 72, 153, 0.16) 0%, transparent 65%),
            radial-gradient(30% 30% at 22% 78%, rgba(59, 130, 246, 0.16) 0%, transparent 65%);
        background-repeat: repeat, no-repeat, no-repeat, no-repeat, no-repeat;
        background-attachment: fixed;
    }

    [data-testid="stHeader"] { background: transparent !important; }

    /* ===== TYPOGRAPHY ===== */
    html, body, .stApp { font-family: var(--font-body); color: rgba(229, 231, 235, 0.92); }

    .stApp h1 {
        font-family: var(--font-display);
        font-weight: 600;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #FFFFFF 0%, #C7D2FE 55%, #A78BFA 100%);
        -webkit-background-clip: text;
        background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .stApp h2, .stApp h3 {
        font-family: var(--font-display);
        font-weight: 600;
        letter-spacing: -0.01em;
        color: var(--text-primary);
    }
    .stApp h4, .stApp h5 {
        font-family: var(--font-display);
        font-weight: 500;
        color: var(--text-primary);
    }
    [data-testid="stCaptionContainer"] { color: var(--text-secondary) !important; }
    [data-testid="stWidgetLabel"] p {
        font-family: var(--font-mono);
        font-size: 0.72rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--text-secondary);
    }

    /* ===== SIDEBAR: full-height glass pane ===== */
    [data-testid="stSidebar"] {
        background: rgba(13, 17, 28, 0.55) !important;
        backdrop-filter: blur(24px) saturate(180%);
        -webkit-backdrop-filter: blur(24px) saturate(180%);
        border-right: 1px solid var(--glass-border);
    }
    [data-testid="stSidebar"] > div { background: transparent; }
    [data-testid="stSidebar"] img { border-radius: 10px; }

    /* ===== GLASS CARDS (containers keyed glass_*) ===== */
    [class*="st-key-glass_"] {
        background: var(--glass-fill);
        backdrop-filter: blur(16px) saturate(180%);
        -webkit-backdrop-filter: blur(16px) saturate(180%);
        border: 1px solid var(--glass-border);
        border-radius: 18px;
        padding: 1.4rem 1.6rem;
        box-shadow: var(--shadow-glass);
        transition: transform 0.4s var(--ease-premium),
                    border-color 0.4s var(--ease-premium),
                    box-shadow 0.4s var(--ease-premium),
                    backdrop-filter 0.4s var(--ease-premium);
    }
    [class*="st-key-glass_"]:hover {
        transform: translateY(-3px);
        border-color: var(--glass-border-hover);
        backdrop-filter: blur(16px) saturate(220%);
        -webkit-backdrop-filter: blur(16px) saturate(220%);
        box-shadow: var(--shadow-glass-hover);
    }

    /* Reusable glass panel for raw-HTML blocks */
    .glass-panel {
        background: var(--glass-fill);
        backdrop-filter: blur(16px) saturate(180%);
        -webkit-backdrop-filter: blur(16px) saturate(180%);
        border: 1px solid var(--glass-border);
        border-radius: 18px;
        padding: 1.6rem 1.8rem;
        box-shadow: var(--shadow-glass);
    }
    .score-card {
        text-align: center;
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.16), rgba(34, 211, 238, 0.08)), var(--glass-fill);
        border-color: rgba(52, 211, 153, 0.28);
    }
    .score-card h3 { font-family: var(--font-display); color: var(--text-primary); margin: 0; }
    .study-tips { margin-top: 2rem; text-align: center; }
    .study-tips h3 { font-family: var(--font-display); color: var(--text-primary); }
    .study-tips p { color: var(--text-secondary); margin: 0.3rem 0; }
    .study-tips strong { color: rgba(229, 231, 235, 0.95); }

    /* ===== TABS: glass rail with gradient-lit active pill ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.35rem;
        background: var(--glass-fill);
        backdrop-filter: blur(16px) saturate(180%);
        -webkit-backdrop-filter: blur(16px) saturate(180%);
        border: 1px solid var(--glass-border);
        border-radius: 16px;
        padding: 0.35rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: var(--font-display);
        font-weight: 500;
        color: var(--text-secondary);
        border-radius: 11px;
        padding: 0.35rem 1rem;
        background: transparent;
        border: 1px solid transparent;
        transition: all 0.4s var(--ease-premium);
    }
    .stTabs [data-baseweb="tab"]:hover { color: var(--text-primary); background: rgba(255, 255, 255, 0.05); }
    .stTabs [aria-selected="true"] {
        color: var(--text-primary) !important;
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.38), rgba(34, 211, 238, 0.16)) !important;
        border: 1px solid rgba(255, 255, 255, 0.14) !important;
    }
    .stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

    /* ===== BUTTONS ===== */
    .stButton > button, .stDownloadButton > button {
        font-family: var(--font-body);
        font-weight: 600;
        letter-spacing: 0.02em;
        color: var(--text-primary);
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
        padding: 0.65rem 1.6rem;
        backdrop-filter: blur(12px) saturate(160%);
        -webkit-backdrop-filter: blur(12px) saturate(160%);
        box-shadow: 0 10px 24px -10px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.06);
        transition: all 0.4s var(--ease-premium);
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        transform: translateY(-2px);
        border-color: var(--glass-border-hover);
        background: rgba(255, 255, 255, 0.08);
        box-shadow: 0 16px 32px -12px rgba(0, 0, 0, 0.6),
                    0 0 24px -8px rgba(139, 92, 246, 0.35),
                    inset 0 1px 0 rgba(255, 255, 255, 0.10);
    }
    .stButton > button:active, .stDownloadButton > button:active { transform: translateY(0); }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #7C3AED 0%, #4F46E5 55%, #0891B2 100%);
        border: 1px solid rgba(255, 255, 255, 0.18);
        box-shadow: 0 14px 34px -10px rgba(124, 58, 237, 0.55), inset 0 1px 0 rgba(255, 255, 255, 0.20);
    }
    .stButton > button[kind="primary"]:hover {
        filter: brightness(1.08);
        box-shadow: 0 18px 44px -10px rgba(124, 58, 237, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.25);
    }

    /* ===== QUIZ RADIO OPTIONS: selectable glass rows ===== */
    [data-testid="stRadio"] [role="radiogroup"] { gap: 0.5rem; }
    [data-testid="stRadio"] label[data-baseweb="radio"] {
        width: 100%;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 12px;
        padding: 0.7rem 1rem;
        margin: 0;
        transition: all 0.4s var(--ease-premium);
    }
    [data-testid="stRadio"] label[data-baseweb="radio"]:hover {
        background: rgba(255, 255, 255, 0.06);
        border-color: var(--glass-border-hover);
        transform: translateX(4px);
    }
    [data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) {
        border-color: rgba(167, 139, 250, 0.55);
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.16), rgba(34, 211, 238, 0.08));
        box-shadow: 0 0 24px -10px rgba(139, 92, 246, 0.45);
    }
    [data-testid="stRadio"] label p { color: rgba(229, 231, 235, 0.92); }

    /* ===== INPUTS, SELECTS, UPLOADER ===== */
    [data-baseweb="select"] > div, .stTextInput input {
        background-color: rgba(17, 24, 39, 0.55) !important;
        border-color: var(--glass-border) !important;
        border-radius: 12px !important;
        color: var(--text-primary);
        transition: border-color 0.4s var(--ease-premium);
    }
    div[data-baseweb="popover"] ul {
        background-color: rgba(13, 18, 32, 0.92);
        backdrop-filter: blur(20px) saturate(180%);
        -webkit-backdrop-filter: blur(20px) saturate(180%);
        border: 1px solid var(--glass-border);
        border-radius: 12px;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px dashed rgba(255, 255, 255, 0.16);
        border-radius: 14px;
        backdrop-filter: blur(12px) saturate(160%);
        -webkit-backdrop-filter: blur(12px) saturate(160%);
        transition: all 0.4s var(--ease-premium);
    }
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: rgba(167, 139, 250, 0.5);
        background: rgba(124, 58, 237, 0.06);
    }

    /* ===== ALERTS & DIVIDERS (keep semantic colors, soften shape) ===== */
    [data-testid="stAlert"] { border-radius: 12px; }
    div[data-baseweb="notification"] {
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .stApp hr { border-color: rgba(255, 255, 255, 0.07); }

    /* ===== SCROLLBAR ===== */
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.12);
        border-radius: 999px;
        border: 2px solid rgba(0, 0, 0, 0);
        background-clip: padding-box;
    }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.22); background-clip: padding-box; border: 2px solid rgba(0, 0, 0, 0); }

    @media (prefers-reduced-motion: reduce) {
        .stApp * { transition: none !important; animation: none !important; }
    }
    </style>
""", unsafe_allow_html=True)

# ============== SESSION STATE INITIALIZATION ==============
if 'quiz_answers' not in st.session_state:
    st.session_state.quiz_answers = {}
if 'quiz_submitted' not in st.session_state:
    st.session_state.quiz_submitted = False
if 'language' not in st.session_state:
    st.session_state.language = "Bengali"
if 'ollama_model' not in st.session_state:
    st.session_state.ollama_model = OLLAMA_MODEL
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'current_quiz' not in st.session_state:
    st.session_state.current_quiz = None
if 'parsed_questions' not in st.session_state:
    st.session_state.parsed_questions = []

# ============== HEADER ==============
col1, col2 = st.columns([3, 1])
with col1:
    st.title("📚 AI Quiz & Note Master")
    st.markdown("*Transform your handwritten notes into comprehensive study materials with AI-powered summaries, quizzes, and audio.*")

with col2:
    st.empty()

st.divider()

# ============== SIDEBAR ==============
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Language toggle
    st.subheader("🌐 Language")
    language_option = st.selectbox(
        "Select Language",
        ("🇧🇩 Bengali", "🇬🇧 English"),
        index=0 if st.session_state.language == "Bengali" else 1,
        help="Choose your preferred language"
    )
    st.session_state.language = "Bengali" if "Bengali" in language_option else "English"

    st.subheader("Ollama Model")
    available_models = get_ollama_models()
    current_model = st.session_state.ollama_model or OLLAMA_MODEL

    if available_models:
        preferred_candidates = [
            OLLAMA_MODEL,
            "minicpm-v:latest",
            "minicpm-v",
            "moondream:latest",
            "moondream",
            "llava:latest",
            "llava",
            "bakllava:latest",
            "bakllava",
        ]
        preferred_model = next((name for name in preferred_candidates if name in available_models), None)
        vision_markers = ("moondream", "llava", "bakllava", "minicpm", "qwen2.5vl", "gemma3")
        selected_model_looks_visual = any(marker in current_model.lower() for marker in vision_markers)

        if preferred_model and (current_model not in available_models or not selected_model_looks_visual):
            st.info(f"Using vision model '{preferred_model}' for uploaded images.")
            current_model = preferred_model
            st.session_state.ollama_model = current_model
        elif current_model not in available_models:
            st.warning(f"Configured model '{current_model}' is not installed. Using '{available_models[0]}' instead.")
            current_model = available_models[0]
            st.session_state.ollama_model = current_model

        st.session_state.ollama_model = st.selectbox(
            "Select Local Model",
            available_models,
            index=available_models.index(current_model),
            help="Use a vision-capable Ollama model for uploaded note images."
        )
        st.caption("Uploaded note images need a vision-capable model, such as llava or another Ollama vision model.")
    else:
        st.session_state.ollama_model = st.text_input(
            "Model Name",
            value=current_model,
            help="Start Ollama to auto-detect installed models. Image uploads need a vision-capable model."
        ).strip() or OLLAMA_MODEL
    
    st.divider()
    
    # File upload section
    st.subheader("📤 Upload Your Notes")
    images = st.file_uploader(
        "Upload photos of your notes (JPG, PNG)",
        type=['jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        help="Upload up to 3 images for best results"
    )
    
    pil_images = []
    
    if images:
        if len(images) > 3:
            st.error("⚠️ Maximum 3 images allowed")
        else:
            st.success(f"✅ {len(images)} image(s) uploaded")
            
            # Display thumbnails
            st.subheader("Uploaded Images Preview")
            cols = st.columns(len(images))
            
            for i, img in enumerate(images):
                with cols[i]:
                    st.image(img, use_column_width=True)
                    pil_images.append(Image.open(img))
    
    st.divider()
    
    # Quiz difficulty selection
    st.subheader("🎯 Quiz Settings")
    selected_option = st.selectbox(
        "Select Quiz Difficulty",
        ("🟢 Easy", "🟡 Medium", "🔴 Hard"),
        index=None,
        help="Difficulty affects quiz complexity"
    )
    
    # Additional options
    st.subheader("📋 Features")
    generate_flashcards = st.checkbox("📇 Generate Flashcards", value=True)
    generate_keypoints = st.checkbox("⭐ Extract Key Points", value=True)
    
    st.divider()
    
    # Process button
    pressed = st.button(
        "🚀 Generate Content",
        type="primary",
        use_container_width=True,
        help="Click to generate notes, audio, and quiz"
    )
    
    # Footer info
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: rgba(156, 163, 175, 0.8); font-size: 0.85rem;'>
    <p>💡 <strong>Tip:</strong> Upload clear images for best results</p>
    <p>🔐 All data is processed securely</p>
    </div>
    """, unsafe_allow_html=True)

# ============== MAIN CONTENT ==============
# Streamlit reruns this script on every widget interaction (including quiz radio
# clicks), and st.button is only True on the run right after the click — so all
# generated content must live in session state, not behind `if pressed:`.
if 'content_generated' not in st.session_state:
    st.session_state.content_generated = False
if 'difficulty_label' not in st.session_state:
    st.session_state.difficulty_label = None
if 'generated_notes' not in st.session_state:
    st.session_state.generated_notes = None
if 'audio_transcript' not in st.session_state:
    st.session_state.audio_transcript = None
if 'current_quiz_raw' not in st.session_state:
    st.session_state.current_quiz_raw = None
if 'flashcards' not in st.session_state:
    st.session_state.flashcards = None
if 'key_points' not in st.session_state:
    st.session_state.key_points = None


def tame_ai_markdown(text):
    """Demote large markdown headings (#, ##, ###) in AI output to ####
    so the page-title CSS doesn't render them as gigantic gradient text."""
    return re.sub(r"(?m)^(\s{0,3})#{1,3}(?=\s)", r"\1####", text)


def reset_quiz_state():
    st.session_state.current_quiz_raw = None
    st.session_state.parsed_questions = []
    st.session_state.user_answers = {}
    st.session_state.quiz_submitted = False
    for key in list(st.session_state.keys()):
        if key.startswith("quiz_q_"):
            del st.session_state[key]


if pressed:
    # Validation
    if not images:
        st.error("❌ Please upload at least 1 image")
    elif not selected_option:
        st.error("❌ Please select a quiz difficulty")
    else:
        st.session_state.content_generated = True
        st.session_state.difficulty_label = selected_option
        st.session_state.generated_notes = None
        st.session_state.audio_transcript = None
        st.session_state.flashcards = None
        st.session_state.key_points = None
        reset_quiz_state()

if st.session_state.content_generated:
    difficulty_label = st.session_state.difficulty_label
    difficulty = difficulty_label.split()[-1]

    # Create tabs for better organization
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Notes Summary", "🔊 Audio", "🧠 Quiz", "📇 Flashcards", "⭐ Key Points"])

    # ============== TAB 1: NOTES ==============
    with tab1:
        st.subheader("📝 AI-Generated Notes Summary")

        if st.session_state.generated_notes is None:
            if pil_images:
                with st.spinner("✨ AI is analyzing your notes..."):
                    st.session_state.generated_notes = note_generator(pil_images, st.session_state.language, st.session_state.ollama_model)
            else:
                st.error("❌ Images are no longer uploaded. Please re-upload and click Generate Content again.")

        generated_notes = st.session_state.generated_notes

        if generated_notes:
            # Render with st.markdown directly — embedding the text inside a
            # raw HTML <div> stops markdown (**, #, -) from being processed
            with st.container(key="glass_notes"):
                st.markdown(tame_ai_markdown(generated_notes))

            col1, col2 = st.columns(2)

            with col1:
                # Download button for notes
                st.download_button(
                    label="📥 Download Notes (TXT)",
                    data=generated_notes,
                    file_name="generated_notes.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            with col2:
                st.info("💡 Save these notes for future reference")

    # ============== TAB 2: AUDIO ==============
    with tab2:
        st.subheader("🔊 Audio Transcription")
        audio_lang_text = "Bengali" if st.session_state.language == "Bengali" else "English"
        st.info(f"Listen to your notes in {audio_lang_text} audio format")

        if st.session_state.audio_transcript is None and generated_notes:
            with st.spinner("🎵 Generating audio..."):
                # Clean markdown for audio generation
                cleaned_notes = generated_notes
                cleaned_notes = cleaned_notes.replace("#", "")
                cleaned_notes = cleaned_notes.replace("*", "")
                cleaned_notes = cleaned_notes.replace("-", "")
                cleaned_notes = cleaned_notes.replace("`", "")

                st.session_state.audio_transcript = audio_transcription(cleaned_notes, st.session_state.language)

        if st.session_state.audio_transcript:
            st.audio(st.session_state.audio_transcript)
            st.success("✅ Audio generated successfully!")
            st.markdown("🎧 **Use this audio for:**")
            st.markdown("- Listening while commuting")
            st.markdown("- Reinforcing learning through audio")
            st.markdown("- Quick revision")

    # ============== TAB 3: QUIZ ==============
    # Rendered as a fragment: interacting with quiz widgets reruns only this
    # function instead of the whole page, so answer clicks stay instant and
    # there is no full-page loading overlay.
    @st.fragment
    def render_quiz(difficulty, difficulty_label, pil_images):
        st.subheader(f"🧠 Interactive Quiz - {difficulty_label} Level")

        # Generate quiz only once
        if st.session_state.current_quiz_raw is None and pil_images:
            with st.spinner("📋 Generating 5 quiz questions..."):
                raw_quiz = quiz_generator(pil_images, difficulty, st.session_state.language, st.session_state.ollama_model)
                if raw_quiz:
                    st.session_state.current_quiz_raw = raw_quiz
                    st.session_state.parsed_questions = parse_quiz_json(raw_quiz)
                    st.session_state.user_answers = {}
                    st.session_state.quiz_submitted = False
                else:
                    st.error("Failed to generate quiz. Please try again.")

        parsed_questions = st.session_state.parsed_questions

        if not parsed_questions:
            st.error("Could not parse quiz questions. Please regenerate.")
            st.button("🔄 Regenerate Quiz", on_click=reset_quiz_state)

        # === BEFORE SUBMISSION ===
        elif not st.session_state.quiz_submitted:
            st.info(f"**Total Questions: {len(parsed_questions)}** (Answer all and click Submit)")
            
            def update_answer(idx):
                """Callback to safely update answer selection"""
                selected = st.session_state[f"quiz_q_{idx}"]
                if selected:
                    st.session_state.user_answers[idx] = selected[0]  # A, B, C, or D
            
            for idx, q in enumerate(parsed_questions):
                with st.container(key=f"glass_q_{idx}"):
                    st.markdown(f"#### Question {idx + 1}")
                    st.write(f"**{q['question']}**")

                    option_list = [f"{key}) {value}" for key, value in q['options'].items()]

                    # Initialize session state for this question if not exists
                    if f"quiz_q_{idx}" not in st.session_state:
                        st.session_state[f"quiz_q_{idx}"] = None

                    st.radio(
                        label=f"Choose answer for Question {idx + 1}",
                        options=option_list,
                        key=f"quiz_q_{idx}",
                        label_visibility="collapsed",
                        on_change=lambda idx=idx: update_answer(idx)
                    )
            
            def submit_quiz():
                # on_click runs before the rerun, so state is updated in time
                # without needing an explicit st.rerun()
                if len(st.session_state.user_answers) == len(parsed_questions):
                    st.session_state.quiz_submitted = True
                else:
                    st.session_state.show_submit_warning = True

            col1, col2 = st.columns(2)
            with col1:
                st.button("✅ Submit Quiz", type="primary", use_container_width=True, on_click=submit_quiz)

            with col2:
                st.button("🔄 Regenerate Quiz", use_container_width=True, on_click=reset_quiz_state)

            if st.session_state.pop("show_submit_warning", False):
                st.warning("⚠️ Please answer all questions before submitting.")
        
        # === AFTER SUBMISSION (Results) ===
        else:
            st.success("🎉 Quiz Submitted Successfully!")
            correct_count = 0
            
            for idx, q in enumerate(parsed_questions):
                user_ans = st.session_state.user_answers.get(idx)
                correct_ans = q["correct_answer"]
                is_correct = user_ans == correct_ans

                if is_correct:
                    correct_count += 1

                with st.container(key=f"glass_r_{idx}"):
                    st.markdown(f"#### Question {idx + 1}")
                    st.write(f"**{q['question']}**")

                    # Show all options with clear feedback
                    for opt_key, opt_text in q['options'].items():
                        if opt_key == user_ans and is_correct:
                            st.success(f"✅ **{opt_key}) {opt_text}** (Your correct answer)")
                        elif opt_key == user_ans and not is_correct:
                            st.error(f"❌ **{opt_key}) {opt_text}** (Your selected answer)")
                        elif opt_key == correct_ans:
                            st.success(f"✅ **{opt_key}) {opt_text}** (Correct answer)")
                        else:
                            st.write(f"   {opt_key}) {opt_text}")

                    st.markdown("**Explanation:**")
                    st.info(q.get("explanation", "No explanation provided."))

                    # Extra feedback for wrong answers (as requested)
                    if not is_correct and user_ans:
                        st.warning(f"**Why your answer was wrong:** The correct choice is **{correct_ans}**. {q.get('explanation', '')}")
            
            # Final score
            score_percentage = (correct_count / len(parsed_questions)) * 100
            st.markdown(f"""
                <div class='glass-panel score-card'>
                <h3>📊 Your Score: {correct_count}/{len(parsed_questions)} ({score_percentage:.1f}%)</h3>
                </div>
            """, unsafe_allow_html=True)
            
            def retake_quiz():
                st.session_state.quiz_submitted = False
                st.session_state.user_answers = {}
                # Clear radio selections so the retake starts fresh; otherwise
                # on_change never fires for re-picking the same option
                for key in list(st.session_state.keys()):
                    if key.startswith("quiz_q_"):
                        del st.session_state[key]

            st.button("🔄 Retake Quiz", use_container_width=True, on_click=retake_quiz)

    with tab3:
        render_quiz(difficulty, difficulty_label, pil_images)

    # ============== TAB 4: FLASHCARDS ==============
    with tab4:
        if generate_flashcards:
            st.subheader("📇 Study Flashcards")
            st.info("Perfect for quick revision and memorization")

            if st.session_state.flashcards is None and pil_images:
                with st.spinner("🎴 Generating flashcards..."):
                    st.session_state.flashcards = flashcard_generator(pil_images, st.session_state.language, st.session_state.ollama_model)

            flashcards = st.session_state.flashcards

            if flashcards:
                with st.container(key="glass_flashcards"):
                    st.markdown(tame_ai_markdown(flashcards))
                
                st.download_button(
                    label="📥 Download Flashcards",
                    data=flashcards,
                    file_name="flashcards.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
                st.success("✅ Flashcards generated!")
                st.markdown("**💡 How to use flashcards:**")
                st.markdown("1. Cover the answer and read the question")
                st.markdown("2. Try to recall the answer")
                st.markdown("3. Reveal the answer to check")
                st.markdown("4. Repeat until memorized")
        else:
            st.info("📇 Enable 'Generate Flashcards' in settings to see this content")
    
    # ============== TAB 5: KEY POINTS ==============
    with tab5:
        if generate_keypoints:
            st.subheader("⭐ Key Points & Summary")
            st.info("Quick reference for important concepts and formulas")

            if st.session_state.key_points is None and pil_images:
                with st.spinner("📌 Extracting key points..."):
                    st.session_state.key_points = key_points_extractor(pil_images, st.session_state.language, st.session_state.ollama_model)

            key_points = st.session_state.key_points

            if key_points:
                with st.container(key="glass_keypoints"):
                    st.markdown(tame_ai_markdown(key_points))
                
                st.download_button(
                    label="📥 Download Key Points",
                    data=key_points,
                    file_name="key_points.txt",
                    mime="text/plain",
                    use_container_width=True
                )
                
                st.success("✅ Key points extracted!")
        else:
            st.info("⭐ Enable 'Extract Key Points' in settings to see this content")
    
    st.divider()
    st.markdown("""
        <div class='glass-panel study-tips'>
        <h3>🎓 Study Tips</h3>
        <p><strong>1. Review Notes First:</strong> Start with the comprehensive notes summary</p>
        <p><strong>2. Listen to Audio:</strong> Reinforce learning with audio version</p>
        <p><strong>3. Study Flashcards:</strong> Use flashcards for quick memorization</p>
        <p><strong>4. Practice Quiz:</strong> Test your knowledge with the quiz</p>
        <p><strong>5. Review Key Points:</strong> Final revision with key points</p>
        </div>
    """, unsafe_allow_html=True)







