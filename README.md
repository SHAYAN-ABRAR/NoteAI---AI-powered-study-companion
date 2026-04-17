# 📚 NoteAI - Smart Study Companion

Transform handwritten notes into comprehensive study materials using AI-powered analysis.

## ✨ Features

- **📝 AI-Generated Notes** - Automatic note summarization in Bengali/English
- **🔊 Audio Learning** - Text-to-speech in multiple languages
- **🧠 Interactive Quizzes** - Auto-generated 3-question quizzes with instant feedback
- **📇 Smart Flashcards** - Quick Q&A pairs for memorization
- **⭐ Key Points Extraction** - Highlights important concepts
- **🌐 Bilingual Support** - Bengali & English language toggle
- **📥 Export Options** - Download notes, quiz, and study materials

## 🛠️ Tech Stack

- **Frontend:** Streamlit (Python UI framework)
- **AI/ML:** Google Gemini API (text generation)
- **Audio:** gTTS (Google Text-to-Speech)
- **Image Processing:** Pillow
- **Data:** Pandas, NumPy

## 🚀 Getting Started

### Prerequisites
```bash
pip install -r requirements.txt
```

### Setup
1. Get your [Gemini API key](https://ai.google.dev)
2. Create `.env` file:
```
GEMINI_API_KEY=your_api_key_here
```

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
- ✅ Automatic API quota error handling

## 📊 API Limits

Google Gemini Free Tier: 20 requests/day

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

## 📝 License

Open source - feel free to use and modify

---

**Created with ❤️ for students and learners**
