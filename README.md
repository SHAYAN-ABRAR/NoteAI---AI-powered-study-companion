<div align="center">

# 📚 NoteAI — Smart Study Companion

**Turn photos of your handwritten notes into summaries, audio, quizzes & flashcards.**
Runs 100% locally on your machine — private, offline-friendly, and free.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.56-FF4B4B?logo=streamlit&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-local%20AI-000000?logo=ollama&logoColor=white)
![Languages](https://img.shields.io/badge/%F0%9F%87%A7%F0%9F%87%A9%20Bengali%20%7C%20%F0%9F%87%AC%F0%9F%87%A7%20English-bilingual-8B5CF6)

</div>

---

## ✨ Features

| | Feature | What you get |
|---|---|---|
| 📝 | **AI Notes Summary** | Structured study notes generated from up to 3 photos of handwritten notes |
| 🔊 | **Audio Learning** | Listen to your notes in Bengali or English — revise while commuting |
| 🧠 | **Interactive Quiz** | 5 auto-generated MCQs with Easy / Medium / Hard difficulty, instant scoring, per-answer explanations, retake & regenerate |
| 📇 | **Smart Flashcards** | Quick Q&A pairs for rapid memorization |
| ⭐ | **Key Points** | Important concepts, formulas, and facts at a glance |
| 🌐 | **Bilingual** | Full Bengali 🇧🇩 and English 🇬🇧 support with one toggle |
| 📥 | **Export** | Download notes, flashcards, and key points as text files |

## 🎨 Design

A luxury dark **glassmorphism** interface, built entirely with custom CSS on top of Streamlit:

- Frosted-glass panels — `backdrop-filter` blur + saturation over glowing ambient orbs
- Matte deep-charcoal stage with a subtle film-grain texture
- Premium type system: **Clash Display** headers, **Satoshi** body, **JetBrains Mono** labels
- Smooth micro-interactions — cards lift, glow, and tint on hover with a custom easing curve
- Every quiz question lives in its own glass card with selectable glass answer rows

## ⚡ Built for speed

- **Instant quiz interactions** — the quiz renders as an isolated fragment, so picking an answer never reloads the page
- **Smart caching** — notes, audio, quiz, flashcards, and key points are generated once per session, not on every click
- **Local inference** — no cloud API quotas, no rate limits, no data leaving your machine

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| UI | [Streamlit](https://streamlit.io) + custom glassmorphism CSS |
| AI / Vision | [Ollama](https://ollama.com) running a local vision model (e.g. `minicpm-v`) |
| Text-to-Speech | gTTS (Google Text-to-Speech) |
| Imaging | Pillow |

## 🚀 Quick Start

**1. Clone & install**
```bash
git clone https://github.com/SHAYAN-ABRAR/NoteAI---AI-powered-study-companion.git
cd NoteAI---AI-powered-study-companion
pip install -r requirements.txt
```

**2. Set up Ollama**

Install [Ollama](https://ollama.com), then pull a vision-capable model:
```bash
ollama pull minicpm-v
```

**3. Configure** — create a `.env` file in the project root:
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=minicpm-v:latest
OLLAMA_TIMEOUT=240
OLLAMA_IMAGE_MAX_SIZE=1280
```

**4. Run**
```bash
python -m streamlit run app.py
```

The app opens at `http://localhost:8501`. You can also switch between any installed Ollama model from the sidebar.

## ⚙️ Configuration

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server address |
| `OLLAMA_MODEL` | `llava` | Vision model used for note images |
| `OLLAMA_TIMEOUT` | `120` | Generation timeout (seconds) |
| `OLLAMA_IMAGE_MAX_SIZE` | `1280` | Max image dimension sent to the model (px) |
| `OLLAMA_NUM_PREDICT` | `700` | Max tokens per generation |

## 📖 How It Works

1. **Upload** — add up to 3 photos of your notes in the sidebar
2. **Configure** — pick language (Bengali / English) and quiz difficulty
3. **Generate** — one click creates notes, audio, quiz, flashcards & key points
4. **Study** — work through the tabs, take the quiz, get instant feedback with explanations
5. **Export** — download everything for offline revision

## 🔒 Privacy

Your notes never leave your computer. All AI processing happens locally through Ollama — there are no cloud API keys, no uploads, and no usage quotas. Speed depends on your hardware and the model you choose.

## 🔮 Roadmap

- [ ] PDF upload support
- [ ] Progress tracking across sessions
- [ ] Spaced-repetition flashcard mode
- [ ] More languages
- [ ] Mobile-friendly layout

---

<div align="center">

**Made for students, by a student.** If NoteAI helps you study, consider giving it a ⭐

</div>
