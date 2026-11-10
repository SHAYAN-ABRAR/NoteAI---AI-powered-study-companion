<div align="center">

# 📚 NoteAI — Smart Study Companion

**Turn photos of your handwritten notes into summaries, audio, quizzes & flashcards.**
Runs on Ollama Cloud, on a local Ollama model, or fully offline — nothing to set up before you try it.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.56-FF4B4B?logo=streamlit&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-cloud%20%7C%20local-000000?logo=ollama&logoColor=white)
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
- **Three ways to run** — Ollama Cloud with an API key, a local Ollama model, or offline mode with no AI model at all

## 🤖 AI modes

NoteAI picks the mode automatically and shows it in the sidebar:

| Mode | When | What happens |
|---|---|---|
| ☁️ **Ollama Cloud** | `OLLAMA_API_KEY` is set | Photos are analysed by an [Ollama Cloud](https://ollama.com) vision model (`gemma4:31b` by default; pick any model in the sidebar). This is what the hosted app uses. |
| 💻 **Local Ollama** | No key, and Ollama is running locally | Photos are analysed by a vision model on your own machine. |
| 📴 **Offline mode** | No key and no Ollama server | NoteAI reads the text in your photos on-device with Tesseract OCR (English + Bengali) and builds the notes, key points, flashcards and fill-in-the-blank quiz from it. Works best on printed or neatly written notes; it can't interpret diagrams like an AI model can. A banner marks offline results. |

If the AI model fails mid-session (network, quota, wrong key), NoteAI shows a warning and falls back to offline results instead of stopping.

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| UI | [Streamlit](https://streamlit.io) + custom glassmorphism CSS |
| AI / Vision | [Ollama](https://ollama.com): Ollama Cloud, or a local vision model (e.g. `minicpm-v`) |
| Offline mode | Tesseract OCR (via `pytesseract`) + extractive text rules |
| Text-to-Speech | gTTS (Google Text-to-Speech) |
| Imaging | Pillow |

## 🚀 Quick Start

**1. Clone & install**
```bash
git clone https://github.com/SHAYAN-ABRAR/NoteAI---AI-powered-study-companion.git
cd NoteAI---AI-powered-study-companion
pip install -r requirements.txt
```

**2. Pick an AI mode** (or skip this step and run in offline mode)

- **Ollama Cloud** — create an API key at [ollama.com](https://ollama.com) (**Settings → API Keys**) and put it in a `.env` file in the project root:
  ```env
  OLLAMA_API_KEY=your_ollama_api_key
  ```
- **Local Ollama** — install [Ollama](https://ollama.com), then pull a vision-capable model:
  ```bash
  ollama pull minicpm-v
  ```
  and optionally configure it in `.env`:
  ```env
  OLLAMA_BASE_URL=http://localhost:11434
  OLLAMA_MODEL=minicpm-v:latest
  OLLAMA_TIMEOUT=240
  OLLAMA_IMAGE_MAX_SIZE=1280
  ```
- **Offline mode** needs [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) with English and Bengali data:
  ```bash
  sudo apt install tesseract-ocr tesseract-ocr-eng tesseract-ocr-ben   # Debian/Ubuntu
  brew install tesseract tesseract-lang                                 # macOS
  ```
  On Windows, use the [Tesseract installer](https://github.com/UB-Mannheim/tesseract/wiki), tick Bengali under additional languages, and add the install folder to `PATH`.

**3. Run**
```bash
python -m streamlit run app.py
```

The app opens at `http://localhost:8501`. With Ollama running, you can switch between any installed model from the sidebar.

## ⚙️ Configuration

Settings are read from Streamlit secrets first, then environment variables / `.env`.

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_API_KEY` | — | Ollama Cloud API key. When set, NoteAI uses Ollama Cloud |
| `OLLAMA_BASE_URL` | `https://ollama.com` with a key, otherwise `http://localhost:11434` | Ollama server address |
| `OLLAMA_MODEL` | `gemma4:31b` with a key, otherwise `llava` | Vision model used for note images |
| `OLLAMA_TIMEOUT` | `120` | Generation timeout (seconds) |
| `OLLAMA_IMAGE_MAX_SIZE` | `1280` | Max image dimension sent to the model (px) |
| `OLLAMA_NUM_PREDICT` | `700` | Max tokens per generation |

## 🌐 Deploy to Streamlit Community Cloud

1. Create the app at [share.streamlit.io](https://share.streamlit.io) from this repo, branch `main`, main file `app.py`.
2. In **App settings → Secrets**, add your key (TOML):
   ```toml
   OLLAMA_API_KEY = "your_ollama_api_key"
   ```
3. `packages.txt` installs Tesseract on the server, so the app still works in offline mode if the key is missing or the AI is unavailable.

> ⚠️ A public app uses *your* API key, so visitors spend your Ollama quota.

## 📖 How It Works

1. **Upload** — add up to 3 photos of your notes in the sidebar
2. **Configure** — pick language (Bengali / English) and quiz difficulty
3. **Generate** — one click creates notes, audio, quiz, flashcards & key points
4. **Study** — work through the tabs, take the quiz, get instant feedback with explanations
5. **Export** — download everything for offline revision

## 🔒 Privacy

- **Local Ollama and offline mode** — your note photos are processed on the machine running the app.
- **Ollama Cloud** — your note photos are sent to Ollama Cloud for analysis.
- **Audio** — the audio tab uses Google Text-to-Speech, so the generated note text is sent to Google to create the speech.

Speed depends on your hardware (local) or your connection (cloud) and the model you choose.

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
