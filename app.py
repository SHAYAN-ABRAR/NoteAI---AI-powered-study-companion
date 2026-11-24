import html
import os
import re

import streamlit as st
from api_calling import OLLAMA_MODEL, DEFAULT_CLOUD_MODEL, get_ai_status, normalize_model_name, note_generator, audio_transcription, quiz_generator, flashcard_generator, key_points_extractor, extract_correct_answers, parse_quiz_json
from PIL import Image

APP_DIR = os.path.dirname(os.path.abspath(__file__))

# ============== PAGE CONFIGURATION ==============
st.set_page_config(
    page_title="NoteAI",
    page_icon=os.path.join(APP_DIR, "static", "favicon.png"),
    layout="centered",
    initial_sidebar_state="auto"
)

# ============== DESIGN: AN EXERCISE-BOOK PAGE ==============
# Colours, the font (Anek Bangla, self-hosted in static/fonts) and widget shapes
# come from .streamlit/config.toml. The CSS below adds the page itself: a red
# margin rule down the left of the column, numbers and marks hung in that margin,
# ruled lines under the notes, OMR-style answer bubbles and index-card flashcards.
st.html("""
<style>
:root {
    --paper: #FFFFFF;
    --blotter: #EFF2F7;
    --ink: #18213F;
    --ink-2: #4A5578;
    --ballpoint: #2A3FAE;
    --redpen: #CC3340;
    --rule: #C9D5E8;
    --highlight: rgba(255, 228, 94, 0.9);
    --highlight-green: rgba(185, 235, 166, 0.95);
    --line: 2rem;          /* ruled-line pitch under the notes */
    --margin: 4.5rem;      /* page edge to the red margin rule */
    --gutter: 1.5rem;      /* margin rule to the writing */
}

/* ---------- The page ---------- */
.stApp [data-testid="stMainBlockContainer"] {
    max-width: calc(42rem + var(--margin) + var(--gutter) + 2rem);
    padding: 4.5rem 2rem 7rem calc(var(--margin) + var(--gutter));
}
/* The red margin rule, drawn on the scrolling area so it runs the full length of the page */
.stApp [data-testid="stMain"] {
    background-image: linear-gradient(rgba(204, 51, 64, 0.55), rgba(204, 51, 64, 0.55));
    background-size: 1.5px 100%;
    background-repeat: no-repeat;
    background-position: max(var(--margin), calc(50% - (42rem + var(--margin) + var(--gutter) + 2rem) / 2 + var(--margin))) 0;
    background-attachment: local;
}
.nai-margin {
    position: absolute;
    top: 0;
    right: calc(100% + var(--gutter) + 0.75rem);
    display: flex;
    align-items: center;
    gap: 0.3rem;
    white-space: nowrap;
}
.nai-num {
    font-size: 1.375rem;
    line-height: 1.75rem;
    font-weight: 650;
    font-variation-settings: "wdth" 78;
    font-feature-settings: "tnum";
    color: var(--ink);
}

/* ---------- Masthead and hero ---------- */
.nai-masthead {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.5rem 1.5rem;
    margin: 0 0 3.25rem;
}
.nai-wordmark {
    font-size: 1.625rem;
    line-height: 1;
    font-weight: 700;
    font-variation-settings: "wdth" 75;
    letter-spacing: 0.01em;
    color: var(--ink);
}
.nai-status {
    display: inline-flex;
    align-items: flex-start;
    gap: 0.5rem;
    margin: 0;
    font-size: 0.875rem;
    line-height: 1.4;
    color: var(--ink-2);
    overflow-wrap: anywhere;
}
.nai-status::before {
    content: "";
    width: 0.5rem;
    height: 0.5rem;
    margin-top: 0.36em;
    border-radius: 50%;
    background: var(--ballpoint);
    flex: none;
}
.nai-status[data-mode="offline"]::before {
    background: transparent;
    box-shadow: inset 0 0 0 1.5px var(--ink-2);
}
.nai-hero h1 {
    margin: 0 0 1.1rem;
    padding: 0;
    max-width: 11em;
    font-size: clamp(2.25rem, 1.4rem + 3vw, 3.5rem);
    line-height: 1.02;
    font-weight: 640;
    font-variation-settings: "wdth" 78;
    letter-spacing: -0.012em;
    color: var(--ink);
    text-wrap: balance;
}
.nai-hero p {
    margin: 0 0 2rem;
    max-width: 34rem;
    font-size: 1.125rem;
    line-height: 1.65;
    color: var(--ink-2);
}

/* ---------- Widgets ---------- */
[data-testid="stWidgetLabel"] p {
    font-size: 0.9375rem;
    font-weight: 500;
    color: var(--ink);
}
/* Streamlit fades captions to 60%; ink-2 is already the muted tone and keeps 4.5:1 contrast */
.stApp [data-testid="stCaptionContainer"] { color: var(--ink-2); opacity: 1; }
[data-testid="stFileUploaderDropzone"] {
    border: 1.5px dashed #AFC0DB;
    background: var(--blotter);
    padding: 1.25rem 1.25rem;
}
[data-testid="stFileUploaderDropzone"]:hover { border-color: var(--ballpoint); }
.st-key-page_previews [data-testid="stFullScreenFrame"] > div { width: auto !important; }
.st-key-page_previews [data-testid="stImage"] { column-gap: 0.75rem; }
.st-key-page_previews [data-testid="stImage"] img {
    border: 1px solid var(--rule);
    border-radius: 3px;
}
.st-key-page_previews [data-testid="stImageCaption"] {
    color: var(--ink-2);
    font-size: 0.8125rem;
}
.stButton button, .stDownloadButton button {
    min-height: 2.75rem;
    padding: 0.55rem 1.25rem;
    font-weight: 600;
    transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}
.stButton button p, .stDownloadButton button p { font-size: 1rem; }
[data-testid="stBaseButton-secondary"] { background: var(--paper); }
[data-testid="stBaseButton-secondary"]:hover {
    border-color: var(--ballpoint);
    color: var(--ballpoint);
    background: var(--paper);
}
.st-key-pack_options { column-gap: 2.5rem !important; row-gap: 1.1rem !important; }
.st-key-create_pack { margin-top: 0.5rem; }
.st-key-create_pack button { padding: 0.6rem 1.6rem; }
[data-testid="stExpander"] details {
    border-color: var(--rule);
    background: var(--paper);
}
[data-testid="stExpander"] summary p { font-weight: 600; }
[data-testid="stAlertContainer"] { border-radius: 8px; }

/* ---------- Tabs ---------- */
.stTabs { margin-top: 0.5rem; }
.stTabs [data-baseweb="tab-list"] {
    gap: 1.75rem;
    border-bottom: 1px solid var(--rule);
    margin-bottom: 1rem;
}
.stTabs [data-baseweb="tab"] {
    padding: 0.25rem 0 0.8rem;
    background: transparent;
    color: var(--ink-2);
}
.stTabs [data-baseweb="tab"] p { font-size: 1rem; font-weight: 500; }
.stTabs [data-baseweb="tab"]:hover { color: var(--ink); }
.stTabs [aria-selected="true"] { color: var(--ink); }
.stTabs [data-baseweb="tab-highlight"] { background-color: var(--ballpoint); height: 2px; }
.stTabs [data-baseweb="tab-border"] { display: none; }

.nai-lead {
    margin: 0 0 1.25rem;
    font-size: 1.0625rem;
    line-height: 1.6;
    color: var(--ink-2);
}

/* ---------- Ruled sheet: notes and key points ---------- */
[class*="st-key-sheet_"] {
    --rule-y: 22px;   /* sits just under the text baseline at 17px / 32px */
    width: calc(100% + var(--margin) + var(--gutter) + 2rem) !important;
    max-width: none;
    margin: 0 -2rem 0 calc(-1 * (var(--margin) + var(--gutter)));
    padding: var(--line) 2rem var(--line) calc(var(--margin) + var(--gutter));
    background-image: linear-gradient(to bottom,
        transparent var(--rule-y),
        var(--rule) var(--rule-y),
        var(--rule) calc(var(--rule-y) + 1px),
        transparent calc(var(--rule-y) + 1px));
    background-size: 100% var(--line);
}
[class*="st-key-sheet_"] [data-testid="stMarkdownContainer"] * {
    font-size: 1.0625rem;
    line-height: var(--line);
}
[class*="st-key-sheet_"] [data-testid="stMarkdownContainer"] :is(p, ul, ol, li, h1, h2, h3, h4, h5, h6, blockquote, pre, table) {
    margin-top: 0;
    margin-bottom: 0;
    padding-top: 0;
    padding-bottom: 0;
}
[class*="st-key-sheet_"] [data-testid="stMarkdownContainer"] > * + * { margin-top: var(--line); }
[class*="st-key-sheet_"] :is(h1, h2, h3, h4, h5, h6) { font-weight: 650; color: var(--ink); }
[class*="st-key-sheet_"] strong { font-weight: 650; color: var(--ink); }
[class*="st-key-sheet_"] [data-testid="stMarkdownContainer"] li { margin-left: 0; padding-left: 0.15rem; }
[class*="st-key-sheet_"] [data-testid="stMarkdownContainer"] ul { padding-left: 1.3rem; margin-left: 0; }
[class*="st-key-sheet_"] ul > li::marker { content: "–  "; color: var(--ink-2); }
/* Section numbers of the notes hang in the margin, like the numbers you write there */
[class*="st-key-sheet_"] [data-testid="stMarkdownContainer"] > ol { list-style: none; padding-left: 0; margin-left: 0; }
[class*="st-key-sheet_"] [data-testid="stMarkdownContainer"] > ol > li { position: relative; margin-left: 0; padding-left: 0; }
[class*="st-key-sheet_"] [data-testid="stMarkdownContainer"] > ol > li::before {
    content: counter(list-item);
    position: absolute;
    right: calc(100% + var(--gutter) + 0.75rem);
    font-size: 1.25rem;
    font-weight: 650;
    font-variation-settings: "wdth" 78;
    font-feature-settings: "tnum";
    color: var(--ink);
}
[class*="st-key-sheet_"] code {
    background: var(--blotter);
    color: var(--ink);
    font-size: 0.9375rem;
}
/* Key points: bold terms get a highlighter stroke */
.st-key-sheet_keypoints strong {
    background: linear-gradient(transparent 30%, var(--highlight) 30%, var(--highlight) 80%, transparent 80%);
    -webkit-box-decoration-break: clone;
    box-decoration-break: clone;
    padding: 0 0.15em;
    margin: 0 -0.05em;
}

/* ---------- Quiz: one exam paper ---------- */
.nai-q { position: relative; margin: 0; }
.stApp .nai-q-text {
    margin: 0;
    font-size: 1.125rem;
    line-height: 1.75rem;
    font-weight: 600;
    color: var(--ink);
}
[class*="st-key-question_"] { gap: 0.6rem; margin-bottom: 1.6rem; }
[class*="st-key-question_"] [data-testid="stRadio"] [role="radiogroup"] { gap: 0.2rem; }
[class*="st-key-question_"] label[data-baseweb="radio"] {
    width: 100%;
    margin: 0;
    padding: 0.4rem 0.6rem 0.4rem 0.35rem;
    border-radius: 8px;
    align-items: center;
    transition: background-color 0.12s ease;
}
[class*="st-key-question_"] label[data-baseweb="radio"]:hover { background: var(--blotter); }
[class*="st-key-question_"] label[data-baseweb="radio"] > div:first-child { display: none; }
[class*="st-key-question_"] label[data-baseweb="radio"]:has(input:focus-visible) {
    outline: 2px solid var(--ballpoint);
    outline-offset: 1px;
}
[class*="st-key-question_"] label[data-baseweb="radio"] p { font-size: 1.0625rem; line-height: 1.5; color: var(--ink); }
/* The option letter renders as an answer-sheet bubble that fills when chosen */
[class*="st-key-question_"] label[data-baseweb="radio"] code,
.nai-bubble {
    display: inline-grid;
    place-items: center;
    flex: none;
    width: 1.75rem;
    height: 1.75rem;
    margin-right: 0.7rem;
    padding: 0;
    border: 1.5px solid #8C96B3;
    border-radius: 50%;
    background: transparent;
    color: var(--ink-2);
    font-family: inherit;
    font-size: 0.8125rem;
    line-height: 1;
    font-weight: 600;
    vertical-align: middle;
}
[class*="st-key-question_"] label[data-baseweb="radio"]:has(input:checked) code {
    background: var(--ballpoint);
    border-color: var(--ballpoint);
    color: #FFFFFF;
}
.st-key-quiz_actions { margin-top: 0.5rem; }

/* Marked paper */
.nai-score {
    display: flex;
    align-items: center;
    gap: 1.25rem;
    margin: 0.25rem 0 2.75rem;
}
.nai-score-mark {
    position: relative;
    display: grid;
    place-items: center;
    width: 9rem;
    height: 5.25rem;
    flex: none;
    color: var(--redpen);
}
.nai-score-num {
    font-size: 2.75rem;
    line-height: 1;
    font-weight: 650;
    font-variation-settings: "wdth" 78;
    font-feature-settings: "tnum";
}
.nai-score-ring {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
    overflow: visible;
}
.nai-score-ring path {
    fill: none;
    stroke: var(--redpen);
    stroke-width: 2.5;
    stroke-linecap: round;
    stroke-dasharray: 520;
    stroke-dashoffset: 520;
    animation: nai-draw 0.75s cubic-bezier(0.45, 0, 0.25, 1) 0.15s forwards;
}
@keyframes nai-draw { to { stroke-dashoffset: 0; } }
.stApp .nai-score-text p { margin: 0; }
.stApp .nai-score-line { font-size: 1.25rem; line-height: 1.4; font-weight: 600; color: var(--ink); }
.stApp .nai-score-sub { font-size: 0.9375rem; line-height: 1.5; color: var(--ink-2); }
.nai-q.is-marked { margin-bottom: 2.25rem; }
.nai-mark { width: 1.5rem; height: 1.5rem; overflow: visible; }
.nai-mark path { fill: none; stroke: var(--redpen); stroke-width: 2.6; stroke-linecap: round; stroke-linejoin: round; }
.stApp ol.nai-choices { list-style: none; margin: 0.6rem 0 0; padding: 0; display: grid; gap: 0.2rem; }
.stApp .nai-choices li {
    display: flex;
    align-items: center;
    gap: 0;
    margin: 0;
    padding: 0.4rem 0.35rem;
    font-size: 1.0625rem;
    line-height: 1.5;
    color: var(--ink-2);
}
.nai-choices li.is-picked .nai-bubble { background: var(--ballpoint); border-color: var(--ballpoint); color: #FFFFFF; }
.nai-choices li.is-correct, .nai-choices li.is-wrong { color: var(--ink); }
.nai-choices li.is-correct .nai-choice-text {
    background: linear-gradient(transparent 22%, var(--highlight-green) 22%, var(--highlight-green) 84%, transparent 84%);
    -webkit-box-decoration-break: clone;
    box-decoration-break: clone;
    padding: 0 0.15em;
}
.nai-choices li.is-wrong .nai-choice-text {
    text-decoration: line-through;
    text-decoration-color: var(--redpen);
    text-decoration-thickness: 2px;
}
.nai-tag {
    margin-left: auto;
    padding-left: 1rem;
    font-size: 0.8125rem;
    font-weight: 500;
    color: var(--ink-2);
    white-space: nowrap;
}
.nai-choices li.is-wrong .nai-tag { color: var(--redpen); }
.nai-choices li.is-correct .nai-tag { color: #2E7D4F; }
.stApp .nai-why {
    margin: 0.75rem 0 0;
    padding: 0;
    font-size: 1rem;
    line-height: 1.65;
    color: var(--ink);
}
.nai-why b { font-weight: 650; }

/* ---------- Flashcards: index cards ---------- */
.nai-cards {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(16.5rem, 1fr));
    align-items: start;
    gap: 1rem;
    margin: 0 0 1.5rem;
}
.nai-card {
    background: var(--paper);
    border: 1px solid var(--rule);
    border-radius: 3px;
}
.nai-card summary {
    display: grid;
    gap: 0.9rem;
    padding: 1rem 1.1rem 0.85rem;
    border-bottom: 1.5px solid rgba(204, 51, 64, 0.55);
    cursor: pointer;
    list-style: none;
}
.nai-card summary::-webkit-details-marker { display: none; }
.nai-card summary:focus-visible { outline: 2px solid var(--ballpoint); outline-offset: 2px; }
.nai-card-q { font-size: 1.0625rem; line-height: 1.5; font-weight: 600; color: var(--ink); }
.nai-card-cue { font-size: 0.875rem; font-weight: 500; color: var(--ballpoint); }
.nai-card summary:hover .nai-card-cue { text-decoration: underline; text-underline-offset: 3px; }
.nai-card[open] .nai-cue-show, .nai-card:not([open]) .nai-cue-hide { display: none; }
.nai-card-a {
    padding: 0.25rem 1.1rem 0.75rem;
    font-size: 1.0625rem;
    line-height: var(--line);
    color: var(--ink);
    background-image: linear-gradient(to bottom,
        transparent 22px, var(--rule) 22px, var(--rule) 23px, transparent 23px);
    background-size: 100% var(--line);
    background-position: 0 0.25rem;
    animation: nai-reveal 0.18s ease-out;
}
@keyframes nai-reveal { from { opacity: 0; transform: translateY(-3px); } to { opacity: 1; transform: none; } }

/* ---------- How to revise ---------- */
.nai-revise { margin: 3.5rem 0 0; }
.nai-revise h3 {
    margin: 0 0 0.75rem;
    padding: 0;
    font-size: 1.375rem;
    line-height: 1.3;
    font-weight: 600;
    font-variation-settings: "wdth" 85;
    color: var(--ink);
}
.stApp .nai-revise ol { list-style: none; counter-reset: step; margin: 0; padding: 0; }
.stApp .nai-revise li {
    position: relative;
    counter-increment: step;
    margin: 0;
    padding: 0.3rem 0;
    font-size: 1rem;
    line-height: 1.75rem;
    color: var(--ink-2);
}
.nai-revise li::before {
    content: counter(step);
    position: absolute;
    top: 0.3rem;
    right: calc(100% + var(--gutter) + 0.75rem);
    font-size: 1.25rem;
    font-weight: 650;
    font-variation-settings: "wdth" 78;
    color: var(--ink);
}
.nai-revise b { font-weight: 600; color: var(--ink); }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] h2 { font-variation-settings: "wdth" 85; }
[data-testid="stSidebar"] h3 { font-size: 1rem; font-weight: 600; margin-top: 0.5rem; }
.nai-side-note { margin: 0; font-size: 0.8125rem; line-height: 1.5; color: var(--ink-2); }

/* ---------- Phones ---------- */
@media (max-width: 640px) {
    :root { --margin: 2.1rem; --gutter: 0.9rem; }
    .stApp [data-testid="stMainBlockContainer"] { padding: 4rem 1rem 6rem calc(var(--margin) + var(--gutter)); }
    [class*="st-key-sheet_"] {
        width: calc(100% + var(--margin) + var(--gutter) + 1rem) !important;
        margin: 0 -1rem 0 calc(-1 * (var(--margin) + var(--gutter)));
        padding: var(--line) 1rem var(--line) calc(var(--margin) + var(--gutter));
    }
    .nai-margin {
        right: calc(100% + var(--gutter) + 0.4rem);
        flex-direction: column-reverse;
        align-items: flex-end;
        gap: 0.1rem;
    }
    .nai-margin .nai-mark { width: 1.15rem; height: 1.15rem; }
    .nai-num { font-size: 1.125rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 1rem; }
    .stTabs [data-baseweb="tab"] p { font-size: 0.9375rem; }
    [class*="st-key-sheet_"] [data-testid="stMarkdownContainer"] > ol > li::before,
    .nai-revise li::before { right: calc(100% + var(--gutter) + 0.4rem); font-size: 1.0625rem; }
    .nai-masthead { margin-bottom: 2.25rem; }
    .nai-score { gap: 0.75rem; }
    .nai-score-mark { width: 7.25rem; height: 4.5rem; }
    .nai-score-num { font-size: 2.25rem; }
    .st-key-create_pack button { width: 100%; }
}

@media (prefers-reduced-motion: reduce) {
    .nai-score-ring path { animation: none; stroke-dashoffset: 0; }
    .nai-card-a { animation: none; }
    .stButton button, .stDownloadButton button, [class*="st-key-question_"] label[data-baseweb="radio"] { transition: none; }
}
</style>
""")

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

# Streamlit reruns this script on every widget interaction (including quiz radio
# clicks), and a button is only True on the run right after the click — so all
# generated content must live in session state, not behind the button.
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


# ============== HELPERS ==============
def tame_ai_markdown(text):
    """Demote large markdown headings (#, ##, ###) in AI output to ####
    so they stay at the size of the notes and sit on the ruled lines."""
    return re.sub(r"(?m)^(\s{0,3})#{1,3}(?=\s)", r"\1####", text)


def reset_quiz_state():
    st.session_state.current_quiz_raw = None
    st.session_state.parsed_questions = []
    st.session_state.user_answers = {}
    st.session_state.quiz_submitted = False
    for key in list(st.session_state.keys()):
        if key.startswith("quiz_q_"):
            del st.session_state[key]


def create_study_pack():
    """Runs before the rerun, so the page switches to the results in the same click."""
    photos = st.session_state.get("note_photos") or []
    difficulty_choice = st.session_state.get("difficulty_choice")
    if not photos:
        st.session_state.create_error = "Add at least one photo of your notes."
    elif len(photos) > 3:
        pass  # the message under the photos already says how many to remove
    elif not difficulty_choice:
        st.session_state.create_error = "Choose a quiz difficulty."
    else:
        st.session_state.content_generated = True
        st.session_state.difficulty_label = difficulty_choice
        st.session_state.generated_notes = None
        st.session_state.audio_transcript = None
        st.session_state.flashcards = None
        st.session_state.key_points = None
        reset_quiz_state()


# **bold** / __bold__ markers, but not runs of underscores such as the "_____"
# blanks in offline fill-in-the-blank questions
_BOLD_RE = re.compile(r"(\*\*|__)(?=[^\s_*])(.+?)(?<=[^\s_*])\1")


def plain(text):
    """Escape AI text for the hand-built HTML blocks and drop markdown bold markers.
    Whitespace is collapsed so a blank line can't end an HTML block in st.markdown."""
    return html.escape(re.sub(r"\s+", " ", _BOLD_RE.sub(r"\2", str(text))).strip())


_CARD_LABEL = r"\s*(?:[-*•]\s*|\d+[.)]\s*)?(?:{words})(?:\s*\d+)?(?:\s*\([^)\n]*\))?\s*[:：]\s*(.*)$"
_CARD_Q_RE = re.compile(_CARD_LABEL.format(words="প্রশ্ন|Question|Q"), re.IGNORECASE)
_CARD_A_RE = re.compile(_CARD_LABEL.format(words="উত্তর|Answer|A"), re.IGNORECASE)


def parse_flashcards(text):
    """Split the flashcard text into (question, answer) pairs.
    Returns [] when the format isn't recognised, so the raw text is shown instead."""
    cards, question, answer, field = [], None, None, None
    for raw_line in _BOLD_RE.sub(r"\2", str(text)).replace("**", "").splitlines():
        line = raw_line.strip()
        q_match, a_match = _CARD_Q_RE.match(line), _CARD_A_RE.match(line)
        if q_match:
            if question and answer:
                cards.append((question, answer))
            question, answer, field = q_match.group(1).strip(), None, "q"
        elif a_match and question is not None:
            answer, field = a_match.group(1).strip(), "a"
        elif not line or re.fullmatch(r"[-*_=]{3,}", line):
            field = None
        elif field == "q":
            question = f"{question} {line}".strip()
        elif field == "a":
            answer = f"{answer} {line}".strip()
    if question and answer:
        cards.append((question, answer))
    return [(q, a) for q, a in cards if q and a]


def ai_status_label(status):
    if status["mode"] == "cloud":
        return "Ollama Cloud" if status["is_ollama_cloud"] else status["host"]
    if status["mode"] == "local":
        return "Local Ollama"
    return "Offline mode"


TICK_SVG = ('<svg class="nai-mark" viewBox="0 0 24 24" role="img" aria-label="Correct">'
            '<path d="M3.5 13.5 C5.6 15.2 7.4 17.2 9 19.6 C12.4 12.9 16.6 7.6 21.5 3.8"/></svg>')
CROSS_SVG = ('<svg class="nai-mark" viewBox="0 0 24 24" role="img" aria-label="Wrong">'
             '<path d="M5 4.5 C9.5 9.3 14 14.2 19 19.5 M18.6 4.8 C13.8 9.4 9.4 14.3 5.2 19.3"/></svg>')
SCORE_RING_SVG = ('<svg class="nai-score-ring" viewBox="0 0 160 90" aria-hidden="true">'
                  '<path d="M118 13 C96 3 46 4 22 20 C2 34 6 62 34 75 C62 88 118 84 142 64 '
                  'C160 48 154 20 120 11 C108 8 94 8 84 10"/></svg>')

# ============== SIDEBAR: SETTINGS ==============
with st.sidebar:
    st.header("Settings", anchor=False)

    st.subheader("AI model", anchor=False)
    ai_status = get_ai_status()
    available_models = ai_status["models"]
    current_model = normalize_model_name(st.session_state.ollama_model or OLLAMA_MODEL)
    server_name = "Ollama Cloud" if ai_status["is_ollama_cloud"] else ai_status["host"]

    if ai_status["mode"] == "cloud":
        st.html(f'<p class="nai-status" data-mode="cloud">Connected to {html.escape(server_name)}</p>')
    elif ai_status["mode"] == "local":
        st.html(f'<p class="nai-status" data-mode="local">Connected to Ollama at {html.escape(ai_status["host"])}</p>')
    elif ai_status["mode"] == "offline":
        st.html('<p class="nai-status" data-mode="offline">Offline mode</p>')
        if ai_status["key_configured"]:
            st.warning(f"Couldn't reach {server_name} ({ai_status['error']}). Using offline mode for now.")
        st.caption(
            "No AI model is connected, so NoteAI reads the text in your "
            "photos on this device and builds the notes, quiz and flashcards from it. Add an "
            "Ollama Cloud key (`OLLAMA_API_KEY`) or start Ollama locally for full AI analysis."
        )
        if not ai_status["ocr"]:
            st.caption("Offline reading needs Tesseract OCR, which isn't installed here.")

    if ai_status["mode"] == "offline":
        pass  # nothing to pick until a model is reachable
    elif available_models:
        preferred_candidates = [
            OLLAMA_MODEL,
            DEFAULT_CLOUD_MODEL,
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
        vision_markers = ("moondream", "llava", "bakllava", "minicpm", "qwen2.5vl", "qwen3-vl", "gemma3", "gemma4", "llama4", "mistral-small3")
        selected_model_looks_visual = any(marker in current_model.lower() for marker in vision_markers)

        if preferred_model and (current_model not in available_models or not selected_model_looks_visual):
            st.caption(f"Using vision model '{preferred_model}' for uploaded images.")
            current_model = preferred_model
            st.session_state.ollama_model = current_model
        elif current_model not in available_models:
            st.warning(f"Configured model '{current_model}' is not installed. Using '{available_models[0]}' instead.")
            current_model = available_models[0]
            st.session_state.ollama_model = current_model

        st.session_state.ollama_model = st.selectbox(
            "Cloud model" if ai_status["mode"] == "cloud" else "Local model",
            available_models,
            index=available_models.index(current_model),
            help="Use a vision-capable Ollama model for uploaded note images."
        )
        st.caption("Note photos need a vision-capable model, such as llava or another Ollama vision model.")
    else:
        st.session_state.ollama_model = st.text_input(
            "Model name",
            value=current_model,
            help="Start Ollama to auto-detect installed models. Image uploads need a vision-capable model."
        ).strip() or OLLAMA_MODEL

    st.subheader("Include in the study pack", anchor=False)
    generate_flashcards = st.checkbox("Flashcards", value=True)
    generate_keypoints = st.checkbox("Key points", value=True)

    st.html('<p class="nai-side-note">All data is processed securely.</p>')

# ============== MASTHEAD ==============
st.html(
    '<header class="nai-masthead">'
    '<span class="nai-wordmark">NoteAI</span>'
    f'<p class="nai-status" data-mode="{ai_status["mode"]}">{html.escape(ai_status_label(ai_status))}</p>'
    '</header>'
)

if not st.session_state.content_generated:
    st.html(
        '<section class="nai-hero">'
        '<h1>Turn photos of your notes into a study pack</h1>'
        '<p>Add up to three pages. You get a summary, a five-question quiz, flashcards, '
        'key points and an audio version, in Bengali or English.</p>'
        '</section>'
    )

# ============== PAGES AND SETTINGS ==============
# Once a study pack exists, this folds away so the results lead the page.
composer = (
    st.expander("Pages and settings", expanded=False)
    if st.session_state.content_generated
    else st.container()
)
with composer:
    images = st.file_uploader(
        "Photos of your notes",
        type=['jpg', 'jpeg', 'png'],
        accept_multiple_files=True,
        key="note_photos",
    )
    st.caption("Up to three pages, JPG or PNG. Clear, well-lit photos read best.")

    pil_images = []

    if images:
        if len(images) > 3:
            extra = len(images) - 3
            st.error(f"NoteAI reads up to three pages at a time. Remove {extra} photo{'s' if extra > 1 else ''} to continue.")
        else:
            with st.container(key="page_previews"):
                st.image(images, width=112, caption=[f"Page {i + 1}" for i in range(len(images))])
            pil_images = [Image.open(img) for img in images]

    # Side by side when there's room, stacked on narrow screens
    with st.container(horizontal=True, gap="large", key="pack_options"):
        language_choice = st.segmented_control(
            "Language",
            ["Bengali", "English"],
            default=st.session_state.language,
            required=True,
            format_func=lambda value: "বাংলা" if value == "Bengali" else "English",
            key="language_choice",
        )
        st.session_state.language = language_choice or st.session_state.language
        st.segmented_control(
            "Quiz difficulty",
            ["Easy", "Medium", "Hard"],
            required=True,
            key="difficulty_choice",
        )

    st.button("Create study pack", type="primary", key="create_pack", on_click=create_study_pack)

    create_error = st.session_state.pop("create_error", None)
    if create_error:
        st.error(create_error)

# ============== RESULTS ==============
if st.session_state.content_generated:
    difficulty_label = st.session_state.difficulty_label
    difficulty = difficulty_label.split()[-1]

    if ai_status["mode"] == "offline":
        st.info(
            "**Offline mode.** These results were built on this device from the text in your "
            "photos, without an AI model. Handwriting, diagrams and formulas may not be read "
            "accurately. Add an Ollama Cloud key or run Ollama locally for full AI analysis."
        )

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Notes", "Audio", "Quiz", "Flashcards", "Key points"])

    # ============== TAB 1: NOTES ==============
    with tab1:
        if st.session_state.generated_notes is None:
            if pil_images:
                with st.spinner("Reading your pages and writing the notes…"):
                    st.session_state.generated_notes = note_generator(pil_images, st.session_state.language, st.session_state.ollama_model)
            else:
                st.error("The photos were removed before the notes were made. Add them again under Pages and settings, then select Create study pack.")

        generated_notes = st.session_state.generated_notes

        if generated_notes:
            # Render with st.markdown directly — embedding the text inside a
            # raw HTML <div> stops markdown (**, #, -) from being processed
            with st.container(key="sheet_notes"):
                st.markdown(tame_ai_markdown(generated_notes))

            st.download_button(
                label="Download notes (.txt)",
                data=generated_notes,
                file_name="generated_notes.txt",
                mime="text/plain",
                icon=":material/download:",
                on_click="ignore",
            )

    # ============== TAB 2: AUDIO ==============
    with tab2:
        audio_lang_text = "Bengali" if st.session_state.language == "Bengali" else "English"
        st.html(f'<p class="nai-lead">Your notes, read aloud in {audio_lang_text}.</p>')

        if st.session_state.audio_transcript is None and generated_notes:
            with st.spinner("Making the audio…"):
                # Clean markdown for audio generation
                cleaned_notes = generated_notes
                cleaned_notes = cleaned_notes.replace("#", "")
                cleaned_notes = cleaned_notes.replace("*", "")
                cleaned_notes = cleaned_notes.replace("-", "")
                cleaned_notes = cleaned_notes.replace("`", "")

                st.session_state.audio_transcript = audio_transcription(cleaned_notes, st.session_state.language)

        if st.session_state.audio_transcript:
            st.audio(st.session_state.audio_transcript)
            st.caption("Play it on the way to class, to go over the notes again, or for a quick revision before an exam.")

    # ============== TAB 3: QUIZ ==============
    # Rendered as a fragment: interacting with quiz widgets reruns only this
    # function instead of the whole page, so answer clicks stay instant and
    # there is no full-page loading overlay.
    @st.fragment
    def render_quiz(difficulty, difficulty_label, pil_images):
        # Generate quiz only once
        if st.session_state.current_quiz_raw is None and pil_images:
            with st.spinner("Writing the quiz questions…"):
                raw_quiz = quiz_generator(pil_images, difficulty, st.session_state.language, st.session_state.ollama_model)
                if raw_quiz:
                    st.session_state.current_quiz_raw = raw_quiz
                    st.session_state.parsed_questions = parse_quiz_json(raw_quiz)
                    st.session_state.user_answers = {}
                    st.session_state.quiz_submitted = False

        parsed_questions = st.session_state.parsed_questions

        if not parsed_questions:
            if st.session_state.current_quiz_raw is None:
                st.error("Couldn't create a quiz from these photos. Select New questions to try again.")
            else:
                st.error("The quiz came back in a format NoteAI couldn't read. Select New questions to try again.")
            st.button("New questions", on_click=reset_quiz_state)

        # === BEFORE SUBMISSION ===
        elif not st.session_state.quiz_submitted:
            total = len(parsed_questions)
            st.html(
                f'<p class="nai-lead">{total} question{"s" if total != 1 else ""} at '
                f'{html.escape(difficulty.lower())} difficulty. Pick one answer for each, then check your answers.</p>'
            )

            def update_answer(idx):
                """Callback to safely update answer selection"""
                selected = st.session_state[f"quiz_q_{idx}"]
                if selected:
                    st.session_state.user_answers[idx] = selected[0]  # A, B, C, or D

            def show_as_bubble(option):
                letter, _, text = option.partition(")")
                return f"`{letter.strip()}` {text.strip()}"

            for idx, q in enumerate(parsed_questions):
                with st.container(key=f"question_{idx}"):
                    st.html(
                        '<div class="nai-q">'
                        f'<span class="nai-margin"><span class="nai-num">{idx + 1}</span></span>'
                        f'<p class="nai-q-text">{plain(q["question"])}</p>'
                        '</div>'
                    )

                    option_list = [f"{key}) {value}" for key, value in q['options'].items()]

                    # Initialize session state for this question if not exists
                    if f"quiz_q_{idx}" not in st.session_state:
                        st.session_state[f"quiz_q_{idx}"] = None

                    st.radio(
                        label=f"Choose answer for Question {idx + 1}",
                        options=option_list,
                        key=f"quiz_q_{idx}",
                        format_func=show_as_bubble,
                        label_visibility="collapsed",
                        width="stretch",
                        on_change=lambda idx=idx: update_answer(idx)
                    )

            def submit_quiz():
                # on_click runs before the rerun, so state is updated in time
                # without needing an explicit st.rerun()
                if len(st.session_state.user_answers) == len(parsed_questions):
                    st.session_state.quiz_submitted = True
                else:
                    st.session_state.show_submit_warning = True

            with st.container(key="quiz_actions", horizontal=True):
                st.button("Check answers", type="primary", on_click=submit_quiz)
                st.button("New questions", on_click=reset_quiz_state)

            if st.session_state.pop("show_submit_warning", False):
                st.warning(f"Answer all {total} questions before checking.")

        # === AFTER SUBMISSION (Results) ===
        else:
            total = len(parsed_questions)
            correct_count = sum(
                1 for idx, q in enumerate(parsed_questions)
                if st.session_state.user_answers.get(idx) == q["correct_answer"]
            )
            score_percentage = (correct_count / total) * 100

            # The mark goes at the top of the paper, circled in red pen.
            # st.markdown keeps the inline SVG marks (st.html strips SVG); all AI
            # text in these blocks is escaped, and each block is one line of HTML
            # so markdown doesn't reinterpret it.
            st.markdown(
                '<div class="nai-score">'
                f'<div class="nai-score-mark"><span class="nai-score-num">{correct_count}/{total}</span>{SCORE_RING_SVG}</div>'
                '<div class="nai-score-text">'
                f'<p class="nai-score-line">{correct_count} of {total} correct ({score_percentage:.0f}%)</p>'
                '<p class="nai-score-sub">Correct answers are highlighted below.</p>'
                '</div></div>',
                unsafe_allow_html=True,
            )

            for idx, q in enumerate(parsed_questions):
                user_ans = st.session_state.user_answers.get(idx)
                correct_ans = q["correct_answer"]
                is_correct = user_ans == correct_ans

                # Show all options with clear feedback
                rows = []
                for opt_key, opt_text in q['options'].items():
                    classes, tag = [], ""
                    if opt_key == user_ans:
                        classes.append("is-picked")
                        tag = "Your answer"
                    if opt_key == correct_ans:
                        classes.append("is-correct")
                        tag = tag or "Correct answer"
                    elif opt_key == user_ans:
                        classes.append("is-wrong")
                    rows.append(
                        f'<li class="{" ".join(classes)}">'
                        f'<span class="nai-bubble">{html.escape(str(opt_key))}</span>'
                        f'<span class="nai-choice-text">{plain(opt_text)}</span>'
                        + (f'<span class="nai-tag">{tag}</span>' if tag else "")
                        + '</li>'
                    )

                explanation = plain(q.get("explanation", "No explanation provided."))
                if is_correct:
                    why = f'<b>Why {html.escape(str(correct_ans))} is right:</b> {explanation}'
                elif user_ans:
                    # Extra feedback for wrong answers (as requested)
                    why = (f'<b>Why your answer was wrong:</b> The correct choice is '
                           f'<b>{html.escape(str(correct_ans))}</b>. {explanation}')
                else:
                    why = f'<b>Explanation:</b> {explanation}'

                st.markdown(
                    '<div class="nai-q is-marked">'
                    f'<span class="nai-margin">{TICK_SVG if is_correct else CROSS_SVG}'
                    f'<span class="nai-num">{idx + 1}</span></span>'
                    f'<p class="nai-q-text">{plain(q["question"])}</p>'
                    f'<ol class="nai-choices">{"".join(rows)}</ol>'
                    f'<p class="nai-why">{why}</p>'
                    '</div>',
                    unsafe_allow_html=True,
                )

            def retake_quiz():
                st.session_state.quiz_submitted = False
                st.session_state.user_answers = {}
                # Clear radio selections so the retake starts fresh; otherwise
                # on_change never fires for re-picking the same option
                for key in list(st.session_state.keys()):
                    if key.startswith("quiz_q_"):
                        del st.session_state[key]

            st.button("Retake quiz", on_click=retake_quiz)

    with tab3:
        render_quiz(difficulty, difficulty_label, pil_images)

    # ============== TAB 4: FLASHCARDS ==============
    with tab4:
        if generate_flashcards:
            if st.session_state.flashcards is None and pil_images:
                with st.spinner("Making the flashcards…"):
                    st.session_state.flashcards = flashcard_generator(pil_images, st.session_state.language, st.session_state.ollama_model)

            flashcards = st.session_state.flashcards

            if flashcards:
                cards = parse_flashcards(flashcards)
                if cards:
                    st.html(
                        '<p class="nai-lead">Answer each question in your head, then select the card to check. '
                        'Repeat until you know them all.</p>'
                        '<div class="nai-cards">'
                        + "".join(
                            '<details class="nai-card"><summary>'
                            f'<span class="nai-card-q">{plain(question)}</span>'
                            '<span class="nai-card-cue"><span class="nai-cue-show">Show answer</span>'
                            '<span class="nai-cue-hide">Hide answer</span></span>'
                            f'</summary><div class="nai-card-a">{plain(answer)}</div></details>'
                            for question, answer in cards
                        )
                        + '</div>'
                    )
                else:
                    with st.container(key="sheet_flashcards"):
                        st.markdown(tame_ai_markdown(flashcards))

                st.download_button(
                    label="Download flashcards (.txt)",
                    data=flashcards,
                    file_name="flashcards.txt",
                    mime="text/plain",
                    icon=":material/download:",
                    on_click="ignore",
                )
        else:
            st.info("Flashcards are switched off. Turn on Flashcards under Include in the study pack in Settings to see them here.")

    # ============== TAB 5: KEY POINTS ==============
    with tab5:
        if generate_keypoints:
            if st.session_state.key_points is None and pil_images:
                with st.spinner("Picking out the key points…"):
                    st.session_state.key_points = key_points_extractor(pil_images, st.session_state.language, st.session_state.ollama_model)

            key_points = st.session_state.key_points

            if key_points:
                st.html('<p class="nai-lead">The important concepts, formulas and facts, for a quick look before an exam.</p>')
                with st.container(key="sheet_keypoints"):
                    st.markdown(tame_ai_markdown(key_points))

                st.download_button(
                    label="Download key points (.txt)",
                    data=key_points,
                    file_name="key_points.txt",
                    mime="text/plain",
                    icon=":material/download:",
                    on_click="ignore",
                )
        else:
            st.info("Key points are switched off. Turn on Key points under Include in the study pack in Settings to see them here.")

    st.html("""
        <section class="nai-revise">
        <h3>How to revise with this pack</h3>
        <ol>
        <li><b>Read the notes first.</b> Start with the summary of your pages.</li>
        <li><b>Listen to the audio.</b> Hearing the notes again helps them stick.</li>
        <li><b>Go through the flashcards.</b> Use them for quick memorisation.</li>
        <li><b>Take the quiz.</b> Test what you remember.</li>
        <li><b>Finish with the key points.</b> A final revision of the important ideas.</li>
        </ol>
        </section>
    """)
