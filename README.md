# 📚 NoteAI - Smart Study Companion

Transform handwritten notes into comprehensive study materials using AI-powered analysis.

## ✨ Features

- **📝 AI-Generated Notes** - Automatic note summarization in Bengali/English
- **🔊 Audio Learning** - Text-to-speech in multiple languages
- **🧠 Interactive Quizzes** - Auto-generated 5-question quizzes with instant feedback
- **📇 Smart Flashcards** - Quick Q&A pairs for memorization
- **⭐ Key Points Extraction** - Highlights important concepts
- **🌐 Bilingual Support** - Bengali & English language toggle
- **📥 Export Options** - Download notes, quiz, and study materials

## 🛠️ Tech Stack

- **Frontend:** Streamlit (Python UI framework)
- **AI/ML:** Ollama local vision model (image understanding + text generation)
- **Audio:** gTTS (Google Text-to-Speech)
- **Image Processing:** Pillow
- **Data:** Pandas, NumPy

## 🚀 Getting Started

### Prerequisites
```bash
pip install -r requirements.txt
```

### Setup
1. Install and start [Ollama](https://ollama.com)
2. Pull a vision-capable model, for example:
```bash
ollama pull minicpm-v
```
3. Create `.env` file:
```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=minicpm-v:latest
OLLAMA_TIMEOUT=240
OLLAMA_IMAGE_MAX_SIZE=1280
```
The app also lets you choose from installed Ollama models in the sidebar when Ollama is running.

### Run
```bash
python -m streamlit run app.py
```

## 📖 How It Works

1. **Upload** - Take photos of your notes (up to 3 images)
2. **Generate** - Select difficulty level and language
3. **Study** - Get notes, audio, quiz, flashcards & key points
4. **Review** - Submit quiz to see answers with explanations
5. **Export** - Download materials for offline access


## 💡 Key Highlights

- ✅ Multi-language support (Bengali & English)
- ✅ Interactive quiz with score calculation
- ✅ Error handling & user-friendly feedback
- ✅ Session state management for smooth UX
- ✅ Professional UI with custom CSS styling
- ✅ Local Ollama connection error handling

## 📊 API Limits

Ollama runs locally, so there is no cloud API quota. Speed depends on your machine and selected model.

## 🎓 Use Cases

- Students studying for exams
- Note digitization & organization
- Quick concept review
- Language learning support
- Study material generation

## 🔮 Future Enhancements

- [ ] PDF upload support
- [ ] Custom difficulty levels
- [ ] Progress tracking
- [ ] Cloud storage integration
- [ ] Mobile app version
- [ ] More languages

