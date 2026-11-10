"""
Offline mode: used when no AI model is reachable (no OLLAMA_API_KEY and no
local Ollama server).

It reads the text in the note photos on this device with Tesseract OCR, then
builds the notes, key points, flashcards and quiz from that text with simple
extractive rules, so the app still works with zero configuration. It cannot
understand diagrams or messy handwriting the way a vision model can; the UI
says so whenever offline results are shown.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import unicodedata
from collections import Counter

from PIL import Image, ImageOps

try:
    import pytesseract
except ImportError:  # optional dependency; offline mode then reports it can't read images
    pytesseract = None

MIN_WORDS = 12          # below this, the photos are treated as unreadable
_OCR_CACHE: dict[str, str] = {}
_OCR_STATE: dict[str, object] = {}

# Characters that separate words. Bengali vowel signs are not "word" characters
# for Python's \w, so tokens are split on punctuation/space instead.
_SEPARATORS = r"\s.,;:!?।॥()\[\]{}<>\"'“”‘’«»…|/\\=+*_#~^`@$%&–—-"
_TOKEN_RE = re.compile(rf"[^{_SEPARATORS}]+")
# List markers, including the "e"/"o"/"©" that OCR often reads a bullet dot as.
_BULLET_RE = re.compile(
    r"^(?:[-•*·▪●◦○➢►]\s*|[eo©«°¢](?=\s+[A-Z0-9ঀ-৿])\s+|\(?\d{1,2}[.)]\s+|\(?[a-zA-Z][.)]\s+)"
)
_SENTENCE_END_RE = re.compile(r"[.!?।॥:]$")
_BENGALI_RE = re.compile(r"[ঀ-৿]")
_LATIN_RE = re.compile(r"[A-Za-z]")

STOPWORDS_EN = set("""
a about above after again against all also am an and any are as at be because been before being below
between both but by can could did do does doing down during each few for from further had has have having
he her here hers him his how i if in into is it its itself just me more most my no nor not now of off on
once only or other our ours out over own same she should so some such than that the their theirs them then
there these they this those through to too under until up very was we were what when where which while who
whom why will with would you your yours etc eg ie use used using also called can may might must shall one two
include includes including let lets make makes made take takes place happen happens
""".split())

STOPWORDS_BN = set("""
এবং ও আর কিন্তু অথবা বা যে যা যার যাকে যিনি এই এটি এটা এর এতে এক একটি একটা কোন কোনো কী কি কেন কিভাবে কীভাবে
সে তার তাদের তারা তাকে তিনি তাঁর তাঁরা আমি আমরা আমার আমাদের তুমি তোমার আপনি আপনার হয় হয়ে হলো হল হচ্ছে
ছিল ছিলো আছে নেই না নয় করে করা করেন করতে করার জন্য থেকে দিয়ে দ্বারা মধ্যে উপর নিচে পরে আগে সঙ্গে সাথে মতো
যখন তখন যদি তবে তাই সব সকল অনেক কিছু খুব আরও এখন সেই ওই সেটি সেটা হবে হতে পারে বলে যায় গেছে দেয় নিয়ে
মাধ্যমে হিসেবে এমন ঘটে প্রয়োজন ব্যবহার তৈরি নিজের অন্য বিভিন্ন প্রভাবিত
""".split())
# Bengali has two encodings of some letters (e.g. য়); compare everything in NFC.
STOPWORDS_BN = {unicodedata.normalize("NFC", word) for word in STOPWORDS_BN}
_TERM_SKIP = {"it", "this", "that", "there", "these", "those", "they", "he", "she", "we", "you", "i", "which", "what"}

LABELS = {
    "English": {
        "topic": "Main Topic",
        "concepts": "Key Concepts",
        "points": "Important Points",
        "summary": "Summary",
        "kp_topics": "Main topics",
        "kp_defs": "Critical formulas/definitions",
        "kp_facts": "Important facts",
        "q_label": "**Question:**",
        "a_label": "**Answer:**",
        "what_is": "What is {term}?",
        "what_are": "What are {term}?",
        "recall": "Recall: {term}",
        "fill": "Fill in the blank: {text}",
        "explain": "Your notes say: “{sentence}”",
        "overview": "These notes cover {topic}, with a focus on {terms}.",
        "and": "and",
        "untitled": "Your notes",
    },
    "Bengali": {
        "topic": "মূল বিষয়",
        "concepts": "মূল ধারণা",
        "points": "গুরুত্বপূর্ণ পয়েন্ট",
        "summary": "সংক্ষিপ্ত সারসংক্ষেপ",
        "kp_topics": "মূল বিষয়গুলি",
        "kp_defs": "গুরুত্বপূর্ণ সূত্র/সংজ্ঞা",
        "kp_facts": "গুরুত্বপূর্ণ তথ্য",
        "q_label": "**প্রশ্ন (Question):**",
        "a_label": "**উত্তর (Answer):**",
        "what_is": "{term} কী?",
        "what_are": "{term} কী?",
        "recall": "{term} কী?",
        "fill": "শূন্যস্থান পূরণ করুন: {text}",
        "explain": "আপনার নোটে লেখা আছে: “{sentence}”",
        "overview": "এই নোটে {topic} নিয়ে আলোচনা করা হয়েছে, বিশেষ করে {terms}।",
        "and": "ও",
        "untitled": "আপনার নোট",
    },
}

# (pattern, question style). Checked in order; the first match wins.
_DEF_PATTERNS = [
    # English: "Photosynthesis is the process ...", "Stomata are tiny pores ..."
    (re.compile(r"^(?P<term>[A-Za-z][A-Za-z0-9 '()/-]{1,48}?)\s+(?P<verb>is defined as|is called|refers to|means|is|are)\s+(?P<definition>.{8,})$"), "verb"),
    # Bengali: "সালোকসংশ্লেষণ হলো ...", "X মানে ..."
    (re.compile(r"^(?P<term>[^\s:]{1,30}(?:\s[^\s:]{1,30}){0,3}?)\s+(?:হলো|হল|হচ্ছে|মানে)\s+(?P<definition>.{6,})$"), "what_is"),
    # Either language: "Term: definition" / "Term - definition" / "Term = definition"
    (re.compile(r"^(?P<term>[^:=–—]{2,40}?)\s*(?::|=|\s[–—-]\s)\s*(?P<definition>.{6,})$"), "recall"),
]


# ----------------------------------------------------------------------------
# OCR
# ----------------------------------------------------------------------------
def ocr_available() -> bool:
    """True when pytesseract is installed and the Tesseract binary runs."""
    if "available" not in _OCR_STATE:
        ok = False
        if pytesseract is not None:
            try:
                pytesseract.get_tesseract_version()
                ok = True
            except Exception:
                ok = False
        _OCR_STATE["available"] = ok
    return bool(_OCR_STATE["available"])


def _installed_languages() -> set:
    if "languages" not in _OCR_STATE:
        try:
            _OCR_STATE["languages"] = set(pytesseract.get_languages(config=""))
        except Exception:
            _OCR_STATE["languages"] = {"eng"}
    return _OCR_STATE["languages"]


def _prepare(image: Image.Image) -> Image.Image:
    """Grayscale, upright, large enough and high-contrast, which helps Tesseract."""
    img = ImageOps.exif_transpose(image) or image
    img = img.convert("L")
    longest = max(img.size)
    if 0 < longest < 1600:
        scale = 1600 / longest
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.Resampling.LANCZOS)
    return ImageOps.autocontrast(img, cutoff=1)


def _ocr(prepared: Image.Image) -> str:
    """Read the image, picking Bengali, English or both from what is on the page."""
    installed = _installed_languages()
    both = "+".join(code for code in ("ben", "eng") if code in installed) or "eng"
    text = pytesseract.image_to_string(prepared, lang=both, config="--psm 3")
    if "ben" in installed and "eng" in installed:
        bengali = len(_BENGALI_RE.findall(text))
        latin = len(_LATIN_RE.findall(text))
        share = bengali / max(1, bengali + latin)
        # A single-script page reads more accurately with only that script's model.
        if share >= 0.6:
            text = pytesseract.image_to_string(prepared, lang="ben", config="--psm 3")
        elif share <= 0.1:
            text = pytesseract.image_to_string(prepared, lang="eng", config="--psm 3")
    return text


def extract_text(images, language: str = "English") -> str:
    """OCR every image (results cached per image) and return the cleaned text.

    ``language`` is the output language; the OCR script is detected from the page.
    """
    if not images or not ocr_available():
        return ""
    parts = []
    for image in images:
        digest = hashlib.sha1()
        digest.update(repr((image.size, image.mode)).encode())
        digest.update(image.tobytes())
        key = digest.hexdigest()
        if key not in _OCR_CACHE:
            try:
                _OCR_CACHE[key] = _ocr(_prepare(image))
            except Exception:
                _OCR_CACHE[key] = ""
        parts.append(_OCR_CACHE[key])
    return _clean("\n\n".join(parts))


# ----------------------------------------------------------------------------
# Text helpers
# ----------------------------------------------------------------------------
def _words(text: str) -> list[str]:
    return [tok for tok in _TOKEN_RE.findall(text) if any(ch.isalpha() for ch in tok)]


def _is_wordlike(token: str) -> bool:
    return sum(ch.isalpha() for ch in token) >= 2


def _is_stop(word: str) -> bool:
    low = word.lower()
    return len(low) < 3 or low in STOPWORDS_EN or low in STOPWORDS_BN or not _is_wordlike(low)


def _clean(text: str) -> str:
    text = unicodedata.normalize("NFC", text).replace("\r", "").replace("\x0c", "\n")
    text = re.sub(r"(?<=[a-z])-\n(?=[a-z])", "", text)  # re-join hyphenated words
    lines = []
    for raw in text.split("\n"):
        line = re.sub(r"[ \t]+", " ", raw).strip()
        tokens = _TOKEN_RE.findall(line)
        if not tokens:
            lines.append("")
            continue
        wordlike = sum(_is_wordlike(tok) for tok in tokens)
        if wordlike / len(tokens) >= 0.5 or re.search(r"\w\s*=\s*\w", line):
            lines.append(line)
    cleaned = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def _segments(text: str) -> list[str]:
    """Lines of the notes, with lines that wrapped mid-sentence joined back together."""
    segments: list[str] = []
    previous_length = 0
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            segments.append("")
            previous_length = 0
            continue
        bullet = _BULLET_RE.match(line)
        body = line[bullet.end():].strip() if bullet else line
        continues = (
            segments and segments[-1]
            and not bullet
            and not _SENTENCE_END_RE.search(segments[-1])
            and (body[:1].islower() or previous_length >= 45)
        )
        if continues:
            segments[-1] = f"{segments[-1]} {body}"
        else:
            segments.append(body)
        previous_length = len(line)
    return [seg for seg in segments if seg]


def _sentences(segments: list[str]) -> list[str]:
    sentences = []
    for segment in segments:
        for part in re.split(r"(?<=[.!?।॥])\s+", segment):
            part = part.strip(" -•*·")
            if len(_words(part)) >= 3:
                sentences.append(part)
    return sentences


def _display_form(text: str, phrase: str) -> str:
    """The phrase as it is first written in the notes (keeps capitalisation)."""
    match = re.search(rf"(?<![^{_SEPARATORS}]){re.escape(phrase)}(?![^{_SEPARATORS}])", text, re.IGNORECASE)
    return match.group(0) if match else phrase


class _Analysis:
    """Everything the offline generators need, computed once per text."""

    def __init__(self, text: str):
        self.text = text
        self.segments = _segments(text)
        self.sentences = _sentences(self.segments)
        self.word_count = len([w for w in _words(text) if _is_wordlike(w)])
        self.keywords = self._rank_keywords()
        self.counts = Counter(w.lower() for w in _words(text) if not _is_stop(w))

        scored = []
        for index, sentence in enumerate(self.sentences):
            words = [w.lower() for w in _words(sentence) if not _is_stop(w)]
            if not words:
                continue
            length = len(_words(sentence))
            score = sum(self.counts[w] for w in words) / (len(words) ** 0.5)
            if length < 5 or length > 45:
                score *= 0.6
            score *= 1.0 + 0.15 / (1 + index)  # slight preference for earlier lines
            scored.append((score, index, sentence))
        self.ranked_sentences = [s for _, _, s in sorted(scored, key=lambda t: (-t[0], t[1]))]

        first = self.segments[0] if self.segments else ""
        if first and len(_words(first)) <= 8 and not first.endswith("."):
            self.topic = first.rstrip(":")
        else:
            self.topic = ""

    def _rank_keywords(self) -> list[str]:
        singles: Counter = Counter()
        grams: Counter = Counter()
        for segment in self.segments:
            tokens = [w.lower() for w in _words(segment)]
            for token in tokens:
                if not _is_stop(token):
                    singles[token] += 1
            for size in (3, 2):
                for i in range(len(tokens) - size + 1):
                    gram = tokens[i:i + size]
                    if all(not _is_stop(t) for t in gram):
                        grams[" ".join(gram)] += 1
        phrases = {g: c for g, c in grams.items() if c >= 2}
        # Drop a two-word phrase that only ever appears inside a repeated three-word one.
        for gram in [g for g in phrases if g.count(" ") == 1]:
            if any(gram in longer and phrases[longer] >= phrases[gram] for longer in phrases if longer.count(" ") == 2):
                del phrases[gram]
        scores = {g: c * 1.6 for g, c in phrases.items()}
        for word, count in singles.items():
            covered = max((c for g, c in phrases.items() if word in g.split()), default=0)
            if count - covered >= 1:
                scores[word] = count - covered
        ranked = sorted(scores, key=lambda k: (-scores[k], -len(k), k))
        return [_display_form(self.text, k) for k in ranked]

    @property
    def readable(self) -> bool:
        return self.word_count >= MIN_WORDS and bool(self.sentences)

    def concepts(self, n: int) -> list[str]:
        """Top keywords, leaving out the topic itself and its inflected forms."""
        topic = self.topic.lower()
        return [k for k in self.keywords if not topic or (k.lower() not in topic and topic not in k.lower())][:n]

    def top_sentences(self, n: int) -> list[str]:
        chosen = set(self.ranked_sentences[:n])
        return [s for s in self.sentences if s in chosen][:n]  # keep reading order

    def definitions(self) -> list[tuple[str, str, str]]:
        """(term, definition, question style) triples found in the notes."""
        found, seen = [], set()
        for segment in self.segments:
            for pattern, style in _DEF_PATTERNS:
                match = pattern.match(segment)
                if not match:
                    continue
                term = match.group("term").strip(" -•*·:")
                term = re.sub(r"^(?:the|a|an)\s+", "", term, flags=re.IGNORECASE)
                definition = match.group("definition").strip().rstrip(".।")
                if not (1 <= len(_words(term)) <= 5) or len(_words(definition)) < 2:
                    continue
                if term.lower() in _TERM_SKIP or all(_is_stop(w) for w in _words(term)):
                    continue
                if term.lower() in seen:
                    continue
                if style == "verb":
                    style = "what_are" if match.group("verb") == "are" else "what_is"
                seen.add(term.lower())
                found.append((term, definition, style))
                break
        return found

    def formulas(self) -> list[str]:
        return [seg for seg in self.segments if re.search(r"\w\s*=\s*[\w(]", seg) and len(seg) <= 80]


def _analyse(images, language):
    return _Analysis(extract_text(images, language))


def _join_terms(terms: list[str], language: str) -> str:
    if not terms:
        return ""
    if len(terms) == 1:
        return terms[0]
    return f"{', '.join(terms[:-1])} {LABELS[language]['and']} {terms[-1]}"


def _blank(sentence: str, term: str) -> str | None:
    """Replace the first whole-word occurrence of term with a blank."""
    pattern = re.compile(rf"(?<![^{_SEPARATORS}]){re.escape(term)}(?![^{_SEPARATORS}])", re.IGNORECASE)
    if not pattern.search(sentence):
        return None
    return pattern.sub("_____", sentence, count=1)


# ----------------------------------------------------------------------------
# Public generators. Each returns None when the photos have no readable text.
# ----------------------------------------------------------------------------
def unreadable_message(language: str) -> str:
    if language == "Bengali":
        if not ocr_available():
            return ("অফলাইন মোডে ছবির লেখা পড়ার জন্য Tesseract OCR দরকার, যা এখানে ইনস্টল করা নেই। "
                    "পূর্ণ AI বিশ্লেষণের জন্য একটি Ollama Cloud কী (OLLAMA_API_KEY) যোগ করুন অথবা লোকাল Ollama চালু করুন।")
        return ("এই ছবিগুলো থেকে পর্যাপ্ত লেখা পড়া যায়নি। পরিষ্কার, ভালো আলোয় তোলা ছবি ব্যবহার করুন — "
                "অথবা হাতের লেখা পড়ার জন্য একটি AI মডেল যুক্ত করুন (Ollama Cloud কী বা লোকাল Ollama)।")
    if not ocr_available():
        return ("Offline mode needs Tesseract OCR to read your photos, and it isn't installed here. "
                "Add an Ollama Cloud key (OLLAMA_API_KEY) or start Ollama locally for full AI analysis.")
    return ("Offline mode couldn't read enough text from these photos. Use clear, well-lit photos — "
            "or connect an AI model (Ollama Cloud key or local Ollama) to read handwriting.")


def notes(images, language: str = "English") -> str | None:
    labels = LABELS[language]
    doc = _analyse(images, language)
    if not doc.readable:
        return None
    concepts = doc.concepts(6)
    topic = doc.topic or _join_terms(doc.keywords[:2], language) or labels["untitled"]
    points = doc.top_sentences(5)
    overview = labels["overview"].format(topic=topic, terms=_join_terms(concepts[:3], language))
    best = next((s for s in doc.ranked_sentences if s not in points), "")
    lines = [
        f"1. **{labels['topic']}**", "", f"   {topic}", "",
        f"2. **{labels['concepts']}**", "", f"   {', '.join(concepts)}", "",
        f"3. **{labels['points']}**", "",
        *[f"   - {point}" for point in points], "",
        f"4. **{labels['summary']}**", "", f"   {overview} {best}".rstrip(),
    ]
    return "\n".join(lines)


def key_points(images, language: str = "English") -> str | None:
    labels = LABELS[language]
    doc = _analyse(images, language)
    if not doc.readable:
        return None
    defs = [f"{term}: {definition}" for term, definition, _ in doc.definitions()[:4]]
    defs += [f for f in doc.formulas() if not any(f.endswith(d.split(": ", 1)[-1]) for d in defs)][: max(0, 5 - len(defs))]
    facts = [s for s in doc.top_sentences(6) if not any(s.startswith(d.split(":")[0]) for d in defs)][:5]
    topics = [doc.topic] + doc.concepts(5) if doc.topic else doc.concepts(6)
    lines = [f"- **{labels['kp_topics']}:** {', '.join(topics)}"]
    if defs:
        lines.append(f"- **{labels['kp_defs']}:**")
        lines += [f"  - {item}" for item in defs]
    lines.append(f"- **{labels['kp_facts']}:**")
    lines += [f"  - {fact}" for fact in facts]
    return "\n".join(lines)


def flashcards(images, language: str = "English", count: int = 5) -> str | None:
    labels = LABELS[language]
    doc = _analyse(images, language)
    if not doc.readable:
        return None
    cards: list[tuple[str, str]] = []
    for term, definition, style in doc.definitions():
        cards.append((labels[style].format(term=term), definition))
        if len(cards) == count:
            break
    used_answers = {answer.lower() for _, answer in cards}
    for sentence in doc.ranked_sentences:
        if len(cards) >= count:
            break
        for keyword in doc.keywords[:15]:
            if keyword.lower() in used_answers:
                continue
            cloze = _blank(sentence, keyword)
            if cloze:
                cards.append((labels["fill"].format(text=cloze), keyword))
                used_answers.add(keyword.lower())
                break
    if not cards:
        return None
    blocks = [f"{labels['q_label']} {q}\n\n{labels['a_label']} {a}" for q, a in cards]
    return "\n\n---\n\n".join(blocks)


def quiz(images, difficulty: str = "Medium", language: str = "English", seed=None) -> str | None:
    """Up to 5 fill-in-the-blank MCQs as JSON in the same schema the AI path returns."""
    labels = LABELS[language]
    doc = _analyse(images, language)
    if not doc.readable:
        return None
    rng = random.Random(seed)
    pool = doc.keywords[:20]
    if len(pool) < 4:
        return None

    candidates = doc.ranked_sentences[:12]
    rng.shuffle(candidates)
    questions, used = [], set()
    for sentence in candidates:
        if len(questions) == 5:
            break
        answer = next((k for k in pool if k.lower() not in used and _blank(sentence, k)), None)
        if not answer:
            continue
        others = [k for k in pool if k.lower() != answer.lower() and not _blank(sentence, k)]
        if len(others) < 3:
            continue
        if difficulty == "Hard":      # look-alike options are harder to tell apart
            others.sort(key=lambda k: (abs(len(k) - len(answer)), rng.random()))
            distractors = others[:3]
        elif difficulty == "Easy":    # less related terms make the answer stand out
            distractors = rng.sample(others[len(others) // 2:] if len(others) >= 6 else others, 3)
        else:
            distractors = rng.sample(others, 3)
        options = [answer, *distractors]
        rng.shuffle(options)
        letters = ["A", "B", "C", "D"]
        questions.append({
            "question": labels["fill"].format(text=_blank(sentence, answer)),
            "options": dict(zip(letters, options)),
            "correct_answer": letters[options.index(answer)],
            "explanation": labels["explain"].format(sentence=sentence),
        })
        used.add(answer.lower())
    if not questions:
        return None
    return json.dumps({"questions": questions}, ensure_ascii=False)
