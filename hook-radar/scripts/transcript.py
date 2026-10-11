"""Stage 3 - TRANSCRIPT.

Normalises whatever caption source we have into ONE shape:

    [{"start": 2.42, "end": 2.85, "text": "ninety"}, ...]   word level

Word-level is non-negotiable. Phrase/SRT-level output loses the sub-second gap
data that tells you where a beat actually ends, so every cut edge drifts.
(That lesson is lifted from video-use's hard rules.)

Sources, in order of preference:
  1. YouTube json3 captions  - free, instant, word-level when the track has it
  2. faster-whisper          - local, free, always word-level, slower
"""
from __future__ import annotations

import re
from pathlib import Path

from common import fail, log, read_json, write_json

# ------------------------------------------------------------------ cleaning

# YouTube auto-captions on some channels inject a speaker label before the first
# cue of each turn: "Anton Osika (00:00:00):". It is not speech, it corrupts the
# opening line of any clip that starts there, and it makes a real clip look like
# a context trap. The timestamp token is the reliable anchor - it is never spoken
# content - so we drop it plus the capitalised name run that precedes it.
TS_TOKEN_RE = re.compile(r"^\(?\d{1,2}:\d{2}:\d{2}\)?:?$|^\x00TS\x00$")
NAME_TOKEN_RE = re.compile(r"^[A-Z][\w'.-]*$")


TS_MARKER = "\x00TS\x00"

# YouTube's own annotations for non-speech audio. Two shapes exist:
#   [inaudible 00:12:19], [music], [applause]   <- square brackets
#   (Laughter), (Applause), (Music), (Laughs)   <- round brackets
# Both are metadata, not speech. They corrupt any hook line they land in, and a
# bare "(Laughter)" as an opening line scores as an empty hook. The round-bracket
# form is only stripped when the content is a known non-speech tag, so a real
# parenthetical in speech is never damaged.
ANNOTATION_RE = re.compile(r"\[[^\]]{0,120}\]")
NON_SPEECH_TAGS = {
    "laughter", "laughs", "laughing", "applause", "music", "musical",
    "sighs", "sigh", "crosstalk", "inaudible", "silence", "no audio",
    "clears throat", "coughs", "chuckles", "giggles", "cheering", "cheers",
}
ROUND_TAG_RE = re.compile(r"\(([^()]{0,30})\)")


def _clean(text: str) -> str:
    """Collapse whitespace, keeping caption timestamps as explicit markers.

    The timestamp must survive this step: it is the anchor the speaker-label
    cleaner walks back from. Removing it here would strand the names, which is
    exactly the bug this replaces. Markers are dropped at the end of _finalise.
    """
    text = (text or "").replace("\n", " ")
    text = re.sub(r"\(\d{1,2}:\d{2}:\d{2}\):?", f" {TS_MARKER} ", text)
    text = ANNOTATION_RE.sub(" ", text)
    # drop round-bracket tags only when they name non-speech audio
    text = ROUND_TAG_RE.sub(
        lambda m: " " if m.group(1).strip().lower() in NON_SPEECH_TAGS else m.group(0),
        text,
    )
    return re.sub(r"\s+", " ", text).strip()


def _drop_speaker_stamps(words: list[dict], max_name_tokens: int = 3) -> list[dict]:
    """Remove speaker labels that auto-captions inject before a new turn.

    Two shapes appear in the wild, and both must go:

      1. "Anton Osika (00:00:00):"  -> name run, then a timestamp token
      2. "Lenny Rachitsky You guys hit 4 million ARR" -> name run glued to the
         first real words, because the timestamp cue landed in a previous event

    Shape 1 is anchored on the timestamp. Shape 2 has no anchor, so we detect it
    positionally: a short capitalised run at the very start of a turn, where the
    same names repeat throughout the transcript. We only strip names that we
    have actually seen carrying a timestamp elsewhere - never a one-off name -
    so a sentence beginning with a proper noun is safe.
    """
    # pass 1: collect the names that are confirmed speaker labels (shape 1)
    confirmed: set[str] = set()
    for i, w in enumerate(words):
        if TS_TOKEN_RE.match(w.get("text") or ""):
            j = i - 1
            run = []
            while j >= 0 and len(run) < max_name_tokens and NAME_TOKEN_RE.match(words[j].get("text") or ""):
                run.append(words[j]["text"])
                j -= 1
            if run:
                confirmed.add(" ".join(reversed(run)))

    out: list[dict] = []
    for w in words:
        if TS_TOKEN_RE.match(w.get("text") or ""):
            removed = 0
            while out and removed < max_name_tokens and NAME_TOKEN_RE.match(out[-1].get("text") or ""):
                out.pop()
                removed += 1
            continue
        out.append(w)

    # pass 2: strip confirmed names that survived as plain text (shape 2)
    if not confirmed:
        return out

    # longest names first so "Anton Osika" is matched before "Anton"
    names = sorted(confirmed, key=lambda n: len(n.split()), reverse=True)
    tokens_cache = {n: n.split() for n in names}

    cleaned: list[dict] = []
    i = 0
    while i < len(out):
        matched = False
        for name in names:
            parts = tokens_cache[name]
            n = len(parts)
            if i + n <= len(out) and all(
                (out[i + k].get("text") or "").strip(" :,") == parts[k] for k in range(n)
            ):
                i += n
                matched = True
                break
        if not matched:
            cleaned.append(out[i])
            i += 1
    return cleaned


def _dedupe(words: list[dict]) -> list[dict]:
    """Auto-captions emit rolling repeats. Drop the duplicates, keep the first."""
    out: list[dict] = []
    for w in words:
        if out:
            prev = out[-1]
            same_text = prev["text"].lower() == w["text"].lower()
            overlapping = abs(w["start"] - prev["start"]) < 0.35
            if same_text and overlapping:
                if w["end"] < prev["end"]:
                    out[-1] = w
                continue
        out.append(w)
    return out


def _finalise(words: list[dict]) -> list[dict]:
    """Every transcript path ends here, so cleaning can never be forgotten."""
    words.sort(key=lambda w: w["start"])
    words = _drop_speaker_stamps(words)   # uses the TS marker as its anchor
    words = [w for w in words if not TS_TOKEN_RE.match(w.get("text") or "")]
    return _dedupe(words)


# ------------------------------------------------------------------ json3


def words_from_json3(data: dict) -> list[dict]:
    """YouTube json3 -> word list. Handles both manual and auto-generated tracks."""
    words: list[dict] = []

    for event in data.get("events", []) or []:
        segs = event.get("segs") or []
        if not segs:
            continue
        base_ms = event.get("tStartMs")
        if base_ms is None:
            continue

        for seg in segs:
            text = _clean(seg.get("utf8", ""))
            if not text:
                continue

            offset_ms = seg.get("tOffsetMs")
            start_ms = base_ms + (offset_ms if offset_ms is not None else 0)
            dur_ms = seg.get("dDurationMs")

            # A seg can hold several words; split and distribute time evenly
            # so downstream cut logic still gets a usable boundary per word.
            pieces = [p for p in text.split(" ") if p]
            if not pieces:
                continue
            if dur_ms is None:
                dur_ms = event.get("dDurationMs") or (250 * len(pieces))
            per = dur_ms / max(1, len(pieces))

            for i, piece in enumerate(pieces):
                words.append(
                    {
                        "start": round((start_ms + i * per) / 1000.0, 3),
                        "end": round((start_ms + (i + 1) * per) / 1000.0, 3),
                        "text": piece,
                    }
                )

    return _finalise(words)


# ------------------------------------------------------------------ whisper


def words_from_whisper(
    audio_or_video: Path,
    model_size: str = "small",
    device: str = "auto",
    language: str | None = None,
) -> list[dict]:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        fail(
            "No captions available on this video and faster-whisper is not installed.\n"
            "  Fix one of these:\n"
            "    pip install faster-whisper        (local, free, ~1GB for 'small')\n"
            "    or pick a video that has a caption track"
        )

    if device == "auto":
        try:
            import torch  # noqa: F401

            device = "cuda"
        except Exception:
            device = "cpu"

    log(f"  whisper: model={model_size} device={device} (first run downloads the model)")
    model = WhisperModel(
        model_size, device=device, compute_type="int8" if device == "cpu" else "float16"
    )
    segments, _info = model.transcribe(
        str(audio_or_video),
        word_timestamps=True,
        language=None if (language or "auto") == "auto" else language,
        vad_filter=True,
    )
    words: list[dict] = []
    for seg in segments:
        for w in seg.words or []:
            text = _clean(w.word)
            if not text:
                continue
            words.append(
                {"start": round(float(w.start), 3), "end": round(float(w.end), 3), "text": text}
            )
    return _finalise(words)


def extract_audio(video: Path, out_wav: Path) -> Path:
    from common import run_cmd

    proc = run_cmd(
        [
            "ffmpeg", "-y", "-i", str(video),
            "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
            str(out_wav),
        ]
    )
    if proc.returncode != 0 or not out_wav.exists():
        fail(f"ffmpeg could not extract audio from {video}")
    return out_wav


# ------------------------------------------------------------------ phrases


def build_sentences(words: list[dict]) -> list[dict]:
    """Group words into actual sentences, ending only on terminal punctuation.

    This is a different unit from a phrase and the distinction matters. A phrase
    breaks on any 0.5s pause, which happens mid-clause all the time - "so I told
    him / it was fine" becomes two phrases. A sentence breaks only on . ! ? which
    is the boundary a clip must use if it is going to sound complete.

    Used by the scorer to snap clip edges to genuinely finished thoughts.
    """
    sentences: list[dict] = []
    cur: list[dict] = []

    def flush():
        if not cur:
            return
        sentences.append(
            {
                "start": cur[0]["start"],
                "end": cur[-1]["end"],
                "text": " ".join(w["text"] for w in cur),
                "words": len(cur),
            }
        )
        cur.clear()

    for i, w in enumerate(words):
        cur.append(w)
        text = w["text"]

        if not re.search(r"[.!?][\"\')\]]?$", text):
            continue

        # guard: decimals like "3.5" and abbreviations like "Mr." are not ends
        if re.fullmatch(r"\d+\.", text):
            continue

        # guard: an ellipsis is a trailing-off, not a completed thought.
        # "So we have to..." is the speaker still going, not a boundary.
        if text.endswith(("...", "..")):
            continue

        # guard: a closing quote after terminal punctuation ("amazing!") is a
        # quotation ending, but the sentence may continue - "...amazing!" No, it
        # was very bad." Only treat it as a boundary if the NEXT token starts a
        # new sentence rather than continuing this one.
        nxt = words[i + 1]["text"] if i + 1 < len(words) else ""
        if nxt and not re.match(r"^[A-Z\"(\[]", nxt):
            continue
        # a continuation word after the punctuation means we are mid-sentence
        if nxt.lower() in {"and", "but", "so", "or", "because", "then", "that",
                           "which", "who", "when", "while", "no", "yes"}:
            continue

        flush()
    flush()
    return sentences


def build_phrases(words: list[dict], gap: float = 0.5, max_words: int = 14) -> list[dict]:
    """Group words into readable phrases, breaking on silence >= gap.

    This is the LLM's primary reading view - one line per phrase with its
    [start-end] range, the same shape video-use packs its takes into.
    """
    phrases: list[dict] = []
    cur: list[dict] = []

    def flush():
        if not cur:
            return
        phrases.append(
            {
                "start": cur[0]["start"],
                "end": cur[-1]["end"],
                "text": " ".join(w["text"] for w in cur),
                "words": len(cur),
            }
        )
        cur.clear()

    for w in words:
        if cur:
            silence = w["start"] - cur[-1]["end"]
            if silence >= gap or len(cur) >= max_words or re.search(r"[.!?]$", cur[-1]["text"]):
                flush()
        cur.append(w)
    flush()
    return phrases


def render_packed(phrases: list[dict], meta: dict | None = None, max_chars: int = 60000) -> str:
    """Markdown reading view: [start-end] text, one line per phrase."""
    lines: list[str] = []
    if meta:
        dur = meta.get("duration") or 0
        lines.append(f"# {meta.get('title', 'source')}")
        lines.append(
            f"channel: {meta.get('channel', '?')} | duration: {int(dur)}s | "
            f"views: {meta.get('view_count', '?')}"
        )
        lines.append("")
    for p in phrases:
        lines.append(f"[{p['start']:07.2f}-{p['end']:07.2f}] {p['text']}")
    return "\n".join(lines)[:max_chars]


# ------------------------------------------------------------------ entry


def build(
    fetched: dict,
    run_dir: Path,
    mode: str = "auto",
    whisper_model: str = "small",
    whisper_device: str = "auto",
    language: str = "auto",
    video_path: Path | None = None,
) -> dict:
    """Produce words.json + phrases.json + transcript_packed.md inside run_dir."""
    words_path = run_dir / "words.json"
    phrases_path = run_dir / "phrases.json"
    packed_path = run_dir / "transcript_packed.md"

    if words_path.exists() and phrases_path.exists():
        log("  [cache] transcript")
        sentences_path = run_dir / "sentences.json"
        return {
            "words": read_json(words_path),
            "phrases": read_json(phrases_path),
            "sentences": read_json(sentences_path) if sentences_path.exists() else [],
            "packed_path": str(packed_path),
            "source": "cache",
        }

    words: list[dict] = []
    source = "none"

    want_captions = mode in ("auto", "captions")
    want_whisper = mode in ("auto", "whisper")

    if want_captions and fetched.get("subtitle_path"):
        path = Path(fetched["subtitle_path"])
        if path.exists():
            log(f"  reading captions: {path.name}")
            words = words_from_json3(read_json(path))
            if words:
                source = "captions"

    if not words and want_whisper:
        if video_path is None:
            fail(
                "No word-level captions for this video and no downloaded audio to transcribe.\n"
                "  Re-run with --download-video, or install faster-whisper."
            )
        wav = run_dir / "audio.wav"
        if not wav.exists():
            extract_audio(video_path, wav)
        words = words_from_whisper(wav, whisper_model, whisper_device, language)
        if words:
            source = "whisper"

    if not words:
        fail("Could not build a transcript for this video.")

    phrases = build_phrases(words)
    sentences = build_sentences(words)
    write_json(words_path, words)
    write_json(phrases_path, phrases)
    write_json(run_dir / "sentences.json", sentences)
    packed_path.write_text(render_packed(phrases, fetched.get("meta")), encoding="utf-8")

    log(f"  transcript: {len(words)} words / {len(phrases)} phrases (source: {source})")
    return {
        "words": words,
        "phrases": phrases,
        "sentences": sentences,
        "packed_path": str(packed_path),
        "source": source,
    }
