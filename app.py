import streamlit as st
from api_calling import note_generator, audio_transcription, quiz_generator, flashcard_generator, key_points_extractor, extract_correct_answers, parse_quiz_json
from PIL import Image
import re

# ============== PAGE CONFIGURATION ==============
st.set_page_config(
    page_title="📚 AI Quiz & Note Master",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============== CUSTOM CSS ==============
st.markdown("""
    <style>
    /* Main background and text colors */
    :root {
        --primary-color: #FF6B6B;
        --secondary-color: #4ECDC4;
        --success-color: #2ECC71;
        --warning-color: #F39C12;
        --danger-color: #E74C3C;
    }
    
    /* Custom styling for containers */
    .main {
        padding: 2rem 1rem;
    }
    
    .stContainer {
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Title styling */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    h2, h3 {
        color: #2c3e50;
        font-weight: 600;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
        border: none;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] button {
        border-radius: 8px;
        font-weight: 600;
    }
    
    /* Card styling */
    .card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
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
    <div style='text-align: center; color: #666; font-size: 0.85rem;'>
    <p>💡 <strong>Tip:</strong> Upload clear images for best results</p>
    <p>🔐 All data is processed securely</p>
    </div>
    """, unsafe_allow_html=True)

# ============== MAIN CONTENT ==============
if pressed:
    # Validation
    if not images:
        st.error("❌ Please upload at least 1 image")
    elif not selected_option:
        st.error("❌ Please select a quiz difficulty")
    else:
        # Extract difficulty level
        difficulty = selected_option.split()[-1]
        
        # Create tabs for better organization
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Notes Summary", "🔊 Audio", "🧠 Quiz", "📇 Flashcards", "⭐ Key Points"])
        
        # ============== TAB 1: NOTES ==============
        with tab1:
            st.subheader("📝 AI-Generated Notes Summary")
            
            with st.spinner("✨ AI is analyzing your notes..."):
                generated_notes = note_generator(pil_images, st.session_state.language)
                
                # Display notes with better formatting
                st.markdown(f"""
                    <div style='background-color: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 5px solid #667eea; color: #333333;'>
                    {generated_notes}
                    </div>
                """, unsafe_allow_html=True)
                
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
            
            with st.spinner("🎵 Generating audio..."):
                # Clean markdown for audio generation
                cleaned_notes = generated_notes
                cleaned_notes = cleaned_notes.replace("#", "")
                cleaned_notes = cleaned_notes.replace("*", "")
                cleaned_notes = cleaned_notes.replace("-", "")
                cleaned_notes = cleaned_notes.replace("`", "")
                
                audio_transcript = audio_transcription(cleaned_notes, st.session_state.language)
                
                if audio_transcript:
                    st.audio(audio_transcript)
                    st.success("✅ Audio generated successfully!")
                    st.markdown("🎧 **Use this audio for:**")
                    st.markdown("- Listening while commuting")
                    st.markdown("- Reinforcing learning through audio")
                    st.markdown("- Quick revision")
        
        # ============== TAB 3: QUIZ ==============
               # ============== TAB 3: QUIZ ==============
        with tab3:
            st.subheader(f"🧠 Interactive Quiz - {selected_option} Level")
            
            # Session state for persistence across reruns
            if 'current_quiz_raw' not in st.session_state:
                st.session_state.current_quiz_raw = None
            if 'parsed_questions' not in st.session_state:
                st.session_state.parsed_questions = []
            if 'user_answers' not in st.session_state:
                st.session_state.user_answers = {}
            if 'quiz_submitted' not in st.session_state:
                st.session_state.quiz_submitted = False
            
            # Generate quiz only once
            if st.session_state.current_quiz_raw is None:
                with st.spinner("📋 Generating 5 quiz questions..."):
                    raw_quiz = quiz_generator(pil_images, difficulty, st.session_state.language)
                    if raw_quiz:
                        st.session_state.current_quiz_raw = raw_quiz
                        st.session_state.parsed_questions = parse_quiz_json(raw_quiz)
                        st.session_state.user_answers = {}
                        st.session_state.quiz_submitted = False
                    else:
                        st.error("Failed to generate quiz. Please try again.")
                        st.stop()
            
            parsed_questions = st.session_state.parsed_questions
            
            if not parsed_questions:
                st.error("Could not parse quiz questions. Please regenerate.")
                if st.button("🔄 Regenerate Quiz"):
                    st.session_state.current_quiz_raw = None
                    st.rerun()
                st.stop()
            
            # === BEFORE SUBMISSION ===
            if not st.session_state.quiz_submitted:
                st.info(f"**Total Questions: {len(parsed_questions)}** (Answer all and click Submit)")
                
                def update_answer(idx):
                    """Callback to safely update answer selection"""
                    selected = st.session_state[f"quiz_q_{idx}"]
                    if selected:
                        st.session_state.user_answers[idx] = selected[0]  # A, B, C, or D
                
                for idx, q in enumerate(parsed_questions):
                    st.markdown(f"### Question {idx + 1}")
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
                    
                    st.divider()
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Submit Quiz", type="primary", use_container_width=True):
                        if len(st.session_state.user_answers) == len(parsed_questions):
                            st.session_state.quiz_submitted = True
                            st.rerun()
                        else:
                            st.warning("⚠️ Please answer all questions before submitting.")
                
                with col2:
                    if st.button("🔄 Regenerate Quiz", use_container_width=True):
                        st.session_state.current_quiz_raw = None
                        st.rerun()
            
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
                    
                    st.markdown(f"### Question {idx + 1}")
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
                    
                    st.divider()
                
                # Final score
                score_percentage = (correct_count / len(parsed_questions)) * 100
                st.markdown(f"""
                    <div style='background-color: #d4edda; padding: 20px; border-radius: 10px; text-align: center;'>
                    <h3>📊 Your Score: {correct_count}/{len(parsed_questions)} ({score_percentage:.1f}%)</h3>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("🔄 Retake Quiz", use_container_width=True):
                    st.session_state.quiz_submitted = False
                    st.session_state.user_answers = {}
                    st.rerun()
        
        # ============== TAB 4: FLASHCARDS ==============
        with tab4:
            if generate_flashcards:
                st.subheader("📇 Study Flashcards")
                st.info("Perfect for quick revision and memorization")
                
                with st.spinner("🎴 Generating flashcards..."):
                    flashcards = flashcard_generator(pil_images, st.session_state.language)
                    
                    if flashcards:
                        st.markdown(f"""
                            <div style='background-color: #fff3cd; padding: 20px; border-radius: 10px; border-left: 5px solid #ffc107; color: #333333;'>
                            {flashcards}
                            </div>
                        """, unsafe_allow_html=True)
                        
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
                
                with st.spinner("📌 Extracting key points..."):
                    key_points = key_points_extractor(pil_images, st.session_state.language)
                    
                    if key_points:
                        st.markdown(f"""
                            <div style='background-color: #e7f3ff; padding: 20px; border-radius: 10px; border-left: 5px solid #2196F3; color: #333333;'>
                            {key_points}
                            </div>
                        """, unsafe_allow_html=True)
                        
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
            <div style='text-align: center; background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-top: 2rem; color: #333333;'>
            <h3>🎓 Study Tips</h3>
            <p><strong>1. Review Notes First:</strong> Start with the comprehensive notes summary</p>
            <p><strong>2. Listen to Audio:</strong> Reinforce learning with audio version</p>
            <p><strong>3. Study Flashcards:</strong> Use flashcards for quick memorization</p>
            <p><strong>4. Practice Quiz:</strong> Test your knowledge with the quiz</p>
            <p><strong>5. Review Key Points:</strong> Final revision with key points</p>
            </div>
        """, unsafe_allow_html=True)







