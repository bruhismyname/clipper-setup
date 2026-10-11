"""Stage 4 - SCORE.

Deterministic pre-scoring for candidate clips. The point is NOT to replace the
agent's judgement - it is to hand the agent a ranked shortlist with evidence,
so it spends its reasoning on the top 15 moments instead of all 400.

Four scores, all 0-100:

  hook     - does the opening line open a loop a viewer must resolve?
  retain   - does the audience-retention curve already spike here?
  fit      - does the clip match TikTok's format and pacing reality?
  composite - weighted blend, tuned for TikTok

Design note, borrowed from the tools this was modelled on: never let a single
heuristic decide. Every score ships with the reasons that produced it, so the
agent (or you) can overrule it and see why.
"""
from __future__ import annotations

import re

from common import fmt_time, log, slugify
from heatmap import segment_retention

# ------------------------------------------------------------------ lexicon
#
# Design note. An earlier version scored on keywords alone, which failed in a
# specific and predictable way: "actually" appeared in the surprise AND
# contrarian lists, so a filler phrase like "It's actually really simple" scored
# 47 while a genuinely strong line like "The fastest growing startup in all of
# Europe" scored 30. Frequency of common words is not signal.
#
# What actually predicts whether a line stops a scroll:
#   1. CONCRETE DETAIL   - a number, a name, a specific outcome
#   2. STRUCTURE         - a claim, a reversal, a question, a stake
#   3. NOVELTY           - says something the viewer did not already assume
#   4. EMOTIONAL CHARGE  - stakes, conflict, loss
#   5. DELIVERY SHAPE    - short and punchy beats long and qualified
#
# So: structure carries the weight, and common words are gated so they can only
# contribute when they appear in a meaningful pattern.

# Words so common in speech that alone they mean nothing. They contribute only
# when combined with a structural signal.
WEAK_WORDS = {
    "actually", "really", "very", "just", "like", "thing", "things", "stuff",
    "kind", "sort", "maybe", "probably", "basically", "literally", "simply",
}

# Multi-word phrases that genuinely signal a curiosity gap.
STRONG_PHRASES = {
    "reversal": [
        "turns out", "i was wrong", "we were wrong", "i thought", "everyone thinks",
        "contrary to", "opposite of", "instead of", "not what you", "didn't expect",
    ],
    "withheld": [
        "nobody tells you", "no one tells you", "they don't want you", "what nobody",
        "the truth about", "what they don't", "hidden", "the real reason",
        "the secret", "most people don't",
    ],
    "stakes": [
        "we lost", "i lost", "we almost", "nearly killed", "went bankrupt",
        "cost us", "cost me", "wasted", "blew up", "fell apart", "shut down",
    ],
    "contrarian": [
        "stop doing", "don't do", "never do", "you should never", "is overrated",
        "is underrated", "everyone is wrong", "that's a myth", "i disagree",
    ],
    "proof": [
        "i built", "we built", "i shipped", "we shipped", "i tested", "we tested",
        "i ran", "we ran", "i asked", "i measured",
    ],
}

# Outcome nouns that give a claim something concrete to stand on.
OUTCOME_NOUNS = [
    "arr", "mrr", "revenue", "users", "customers", "growth", "conversion",
    "churn", "retention", "valuation", "funding", "runway", "profit", "margin",
    "downloads", "signups", "followers", "subscribers", "views",
]

WEAK_OPENERS = [
    "so", "and", "but", "um", "uh", "yeah", "okay", "well", "like", "i mean",
    "right", "now", "then", "also", "basically",
]

CONTEXT_TRAPS = [
    "as i said", "like i mentioned", "earlier we", "before we", "in the last video",
    "as you can see here", "this slide", "this chart", "as we discussed",
]

# Closing lines that mean the clip did not actually end on a payoff. "Thank you"
# is the end of a talk, not the end of an idea - a clip stopping there wastes the
# retention it earned. We look for a better boundary nearby, or flag it.
WEAK_CLOSERS = [
    "thank you", "thanks for", "thanks so much", "okay", "alright", "so yeah",
    "you know", "i guess", "anyway", "that's it", "yeah", "mm-hmm", "right",
    "the past", "that time", "something like that",
]

PAYOFF_MARKERS = [
    "so that's", "and that's", "the result", "it worked", "we got", "turns out",
    "and then", "in the end", "the lesson", "that's why", "which means",
]


# ------------------------------------------------------------------ helpers


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower()).strip()


def _hits(text: str, terms: list[str]) -> list[str]:
    return [t for t in terms if t in text]


def _closing_line(boundaries: list[dict], end: float) -> str:
    """The sentence that the clip's end lands on.

    Used for the human-readable closing line, so a reviewer sees the thought the
    clip actually finishes on rather than a slice of words.
    """
    best = None
    for b in boundaries:
        if b["end"] <= end + 0.05:
            if best is None or b["end"] > best["end"]:
                best = b
    return best["text"] if best else ""


def _window_phrases(phrases: list[dict], start: float, end: float) -> list[dict]:
    return [p for p in phrases if p["end"] > start and p["start"] < end]


def _is_lyric(text: str) -> bool:
    """Music transcripts are marked with note glyphs and repeat heavily.

    Lyrics are not hook material for a clipping workflow - they are someone
    else's song, and the moment does not stand alone as speech. Detect and skip
    rather than filling the shortlist with choruses.
    """
    return "\u266a" in text or "\u266b" in text


def detect_content_type(phrases: list[dict], words: list[dict]) -> dict:
    """Classify the source so the agent can say honestly whether this tool fits.

    Returns {type, confidence, reason}. Types: speech | mixed | music | sparse
    """
    if not phrases:
        return {"type": "sparse", "confidence": "high", "reason": "no transcript at all"}

    lyric_phrases = sum(1 for p in phrases if _is_lyric(p["text"]))
    lyric_ratio = lyric_phrases / len(phrases)

    total_seconds = words[-1]["end"] - words[0]["start"] if len(words) > 1 else 0
    words_per_min = (len(words) / total_seconds * 60) if total_seconds > 0 else 0

    if lyric_ratio > 0.5:
        return {
            "type": "music",
            "confidence": "high",
            "reason": f"{lyric_ratio:.0%} of lines are lyrics - this is a song, not speech",
        }
    if lyric_ratio > 0.15:
        return {
            "type": "mixed",
            "confidence": "medium",
            "reason": f"{lyric_ratio:.0%} of lines are lyrics - partly music",
        }
    if words_per_min < 40:
        return {
            "type": "sparse",
            "confidence": "medium",
            "reason": f"only {words_per_min:.0f} words/min - mostly silence or non-speech audio",
        }
    return {
        "type": "speech",
        "confidence": "high",
        "reason": f"{words_per_min:.0f} words/min of continuous speech",
    }


# ------------------------------------------------------------------ scores


def score_hook(first_phrase: str, context_phrases: list[dict]) -> dict:
    """Score the opening line 0-100 on how likely it is to stop a scroll.

    Structure first, keywords second. A line earns points for carrying concrete
    detail, opening a gap, or stating something with stakes - not for containing
    a word that happens to appear on a list.
    """
    raw = (first_phrase or "").strip()
    text = _norm(raw)
    words = text.split()
    reasons: list[str] = []
    signals: dict[str, list[str]] = {}

    if not words:
        return {"score": 0.0, "reasons": ["empty opening line"], "signals": {}}

    score = 25.0   # neutral floor: a plain declarative sentence

    # ---------------------------------------------------------- 1. CONCRETE DETAIL
    # Numbers and outcome nouns are the strongest cheap signal. "We hit 10 million
    # ARR in two months" is checkable; "we grew fast" is not.
    numbers = re.findall(r"\b\d[\d,.]*\s*(?:%|k|m|bn?|million|billion|thousand)?\b", text)
    outcome_hits = _hits(text, OUTCOME_NOUNS)
    magnitude = re.findall(r"\b(?:million|billion|thousand|\d+%|\d+x)\b", text)

    if numbers:
        gain = min(6 + 4 * (len(numbers) - 1), 16)
        # a magnitude word turns a number into a scale claim: "10 million" lands
        # harder than "10" because the size is immediately legible
        if magnitude:
            gain += 6
            reasons.append(f"scale claim ({', '.join(magnitude[:2])}) +6")
        score += gain
        reasons.append(f"concrete number ({', '.join(numbers[:3])}) +{gain}")
        signals.setdefault("concrete", []).extend(numbers[:3])

    # "from X to Y" is a growth story in five words - a very strong short-form shape
    if re.search(r"\bfrom\b.{0,24}\bto\b", text):
        score += 8
        reasons.append("from-X-to-Y growth shape +8")
        signals.setdefault("arc", []).append("from-to")
    if outcome_hits:
        gain = min(6 + 3 * (len(outcome_hits) - 1), 14)
        score += gain
        reasons.append(f"named outcome ({', '.join(outcome_hits[:3])}) +{gain}")
        signals.setdefault("outcome", []).extend(outcome_hits[:3])

    # ---------------------------------------------------------- 2. STRUCTURE
    for label, phrases in STRONG_PHRASES.items():
        hit = _hits(text, phrases)
        if hit:
            weight = {"reversal": 14, "withheld": 15, "stakes": 13,
                      "contrarian": 12, "proof": 8}[label]
            score += weight
            reasons.append(f"{label}: '{hit[0]}' +{weight}")
            signals.setdefault(label, []).extend(hit)

    # a question opens a gap by itself
    if "?" in raw:
        score += 9
        reasons.append("poses a question +9")
        signals.setdefault("question", []).append("?")

    # superlatives and absolutes read as claims worth checking
    superlative = re.search(r"\b(fastest|biggest|largest|best|worst|first|only|most|never|always|every)\b", text)
    if superlative:
        score += 7
        reasons.append(f"absolute claim '{superlative.group(1)}' +7")
        signals.setdefault("absolute", []).append(superlative.group(1))

    # ---------------------------------------------------------- 3. EMOTIONAL CHARGE
    emotion = _hits(text, [
        "love", "hate", "scared", "afraid", "angry", "frustrated", "excited",
        "cried", "terrible", "worst", "amazing", "incredible", "brutal",
    ])
    if emotion:
        score += min(5 + 3 * (len(emotion) - 1), 11)
        reasons.append(f"emotional charge ({', '.join(emotion[:2])}) +{min(5 + 3 * (len(emotion) - 1), 11)}")
        signals.setdefault("emotion", []).extend(emotion)

    # ---------------------------------------------------------- 4. GATED KEYWORDS
    # Common words only count when the line already has structure. This is the
    # fix for the "actually" problem: it can reinforce, never carry.
    has_structure = bool(signals.get("reversal") or signals.get("withheld")
                         or signals.get("stakes") or signals.get("contrarian")
                         or numbers or outcome_hits)
    weak_hits = _hits(text, list(WEAK_WORDS))
    if weak_hits and has_structure:
        score += 3
        reasons.append(f"emphasis word reinforces structure ({', '.join(weak_hits[:2])}) +3")
    elif weak_hits:
        score -= 4
        reasons.append(f"filler word without structure ({', '.join(weak_hits[:2])}) -4")

    # direct address: real, but weaker than structure
    if _hits(text, ["you", "your", "you're", "yourself"]):
        score += 5
        reasons.append("direct address +5")
        signals.setdefault("direct_address", []).append("you")

    # ---------------------------------------------------------- 5. DELIVERY SHAPE
    # short punchy lines hold attention; long qualified ones do not
    n = len(words)
    if n <= 8:
        score += 6
        reasons.append(f"short and punchy ({n} words) +6")
    elif n >= 26:
        score -= 8
        reasons.append(f"long opening ({n} words) -8")
    elif n >= 18:
        score -= 3
        reasons.append(f"longish opening ({n} words) -3")

    # ---------------------------------------------------------- 6. PENALTIES
    first_word = words[0]
    if first_word in WEAK_OPENERS:
        score -= 13
        reasons.append(f"weak opener '{first_word}' -13")
    if re.match(r"^(and|but|so|because)\b", text):
        score -= 7
        reasons.append("starts on a conjunction -7")

    trap = _hits(text, CONTEXT_TRAPS)
    if trap:
        score -= 16
        reasons.append(f"context trap '{trap[0]}' -16")

    if len(words) < 4:
        score -= 8
        reasons.append("opening too thin -8")

    # ---------------------------------------------------------- 7. PAYOFF IN WINDOW
    body = " ".join(_norm(p["text"]) for p in context_phrases)
    if _hits(body, PAYOFF_MARKERS):
        score += 8
        reasons.append("payoff lands inside the window +8")
        signals.setdefault("payoff", []).append("in-window")

    return {
        "score": round(max(0.0, min(100.0, score)), 1),
        "reasons": reasons,
        "signals": signals,
    }


def score_retention(heatmap: list[dict], start: float, end: float) -> dict:
    """0-100. Has YouTube already told us viewers rewatch this window?"""
    if not heatmap:
        return {"score": 50.0, "reasons": ["no heatmap published for this video (neutral 50)"], "stats": None}

    stats = segment_retention(heatmap, start, end)
    delta = stats["delta_vs_baseline"]
    # +0.10 over baseline is a strong signal; scale to 0-100 around a 45 floor
    score = 45.0 + (delta * 350.0)
    if stats["max"] >= 0.95:
        score += 8
    reasons = [
        f"mean intensity {stats['mean']:.2f} vs baseline delta {delta:+.3f}",
        f"peak in window {stats['max']:.2f}",
    ]
    return {"score": round(max(0.0, min(100.0, score)), 1), "reasons": reasons, "stats": stats}


def score_fit(
    duration: float,
    start: float,
    end: float,
    total: float,
    platform: str,
    min_d: float | None = None,
    max_d: float | None = None,
    ideal_d: float | None = None,
) -> dict:
    """0-100. Does this clip match the platform's format reality?

    Two different things are being judged, and they must not be conflated:

      * the user's explicit bounds (--min/--max/--ideal) - a hard contract
      * the platform's typical band - advice, not law

    An earlier version only knew the platform band, so `--min 20 --max 30` was
    silently ignored by the fit score even though the candidate generator
    honoured it. Now the user's numbers govern, and the platform band only
    shapes how much we like a clip that already fits.
    """
    score = 100.0
    reasons: list[str] = []

    # platform advice bands: (floor, ceiling, sweet spot)
    bands = {
        "tiktok": (15, 45, 28),
        "shorts": (20, 60, 40),
        "reels": (15, 60, 30),
    }
    p_lo, p_hi, p_ideal = bands.get(platform, bands["tiktok"])

    # the user's numbers win where given
    lo = min_d if min_d is not None else p_lo
    hi = max_d if max_d is not None else p_hi
    ideal = ideal_d if ideal_d is not None else p_ideal

    if duration < lo:
        under = lo - duration
        score -= 10 + under * 2.0
        reasons.append(f"{duration:.1f}s UNDER requested floor {lo:.0f}s (-{under:.1f}s)")
    elif duration > hi:
        # over the ceiling is a hard failure: the clip cannot be posted at its
        # requested length, so the score has to say so loudly
        over = duration - hi
        score -= 10 + over * 2.0
        reasons.append(f"{duration:.1f}s OVER requested ceiling {hi:.0f}s (+{over:.1f}s)")
    else:
        drift = abs(duration - ideal) / max(1.0, ideal)
        score -= drift * 12
        reasons.append(f"{duration:.1f}s inside {lo:.0f}-{hi:.0f}s (ideal ~{ideal:.0f}s)")

    # if the user asked for something the platform dislikes, say so - but do not
    # override them. It is their call; they just deserve to know the trade-off.
    if hi > p_hi + 5:
        score -= 6
        reasons.append(f"note: >{p_hi}s runs long for {platform}, completion rate drops")
    if lo < p_lo - 5:
        score -= 4
        reasons.append(f"note: <{p_lo}s is short for {platform}")

    # a clip that opens in the last 5% of a long video is usually an outro
    if total and start > total * 0.95:
        score -= 12
        reasons.append("sits in the final 5% of the source (likely outro)")

    return {"score": round(max(0.0, min(100.0, score)), 1), "reasons": reasons}


def composite(hook: float, retain: float, fit: float, has_heatmap: bool) -> float:
    """TikTok weighting: the hook is what gets the watch, retention is what keeps it."""
    if has_heatmap:
        w_hook, w_retain, w_fit = 0.45, 0.35, 0.20
    else:
        # no heatmap -> lean harder on the transcript signals we actually have
        w_hook, w_retain, w_fit = 0.65, 0.10, 0.25
    return round(hook * w_hook + retain * w_retain + fit * w_fit, 1)


# ------------------------------------------------------------------ candidates


def build_candidates(
    words: list[dict],
    phrases: list[dict],
    heatmap: list[dict],
    meta: dict,
    options: dict,
    sentences: list[dict] | None = None,
) -> list[dict]:
    """Generate candidate clip windows from two independent sources of truth.

    A. retention peaks  - YouTube's own audience data
    B. hook phrases     - transcript signals, scanned at every strong line

    They rarely agree, which is the point: the overlap is the gold, and the
    disagreements are worth the agent's attention.
    """
    total = float(meta.get("duration") or (words[-1]["end"] if words else 0))
    min_d = options["min_duration"]
    max_d = options["max_duration"]
    platform = options["platform"]
    has_heatmap = bool(heatmap)

    from heatmap import detect_peaks

    peaks = detect_peaks(heatmap) if heatmap else []
    candidates: list[dict] = []

    # snap against real sentence boundaries when we have them; phrases are the
    # fallback because a phrase can break mid-clause
    boundaries = sentences if sentences else phrases

    def snap_to_phrase(t: float, prefer: str = "start", tolerance: float = 6.0) -> float:
        """Pull a raw time onto the nearest *sentence-ish* boundary.

        Word boundaries are not enough: a window that opens mid-sentence
        ("out all the things that could go wrong") reads as a fragment and kills
        the hook even when the retention data says the moment is good.

        Ending a clip mid-sentence is worse than starting late, so for the END
        edge we search outward until we find a phrase that actually terminates
        a sentence - a full stop, question mark, or exclamation. That is the
        difference between a clip that lands and one that just stops.
        """
        if not boundaries:
            return t

        if prefer == "end":
            # prefer the nearest boundary that finishes a thought AND is not a
            # throwaway sign-off. "Thank you." completes a sentence but carries no
            # payoff, so a clip ending there squanders the attention it earned.
            def is_usable(ph: dict) -> bool:
                text = ph["text"].strip().lower()
                if not re.search(r"[.!?][\"\']?$", text):
                    return False
                bare = text.strip(" .!?\"'")
                if bare in WEAK_CLOSERS or len(bare.split()) <= 3:
                    return False
                # a trailing-off followed by a scrap of speech is not an ending:
                # "So we have to... Hey." leaves the viewer hanging. Only accept
                # it if there is real content after the ellipsis.
                if "..." in text or "…" in text:
                    tail = re.split(r"\.\.\.|…", text)[-1].strip(" .!?\"'")
                    if len(tail.split()) <= 3:
                        return False
                return True

            terminating = [ph for ph in boundaries if is_usable(ph)]
            pool = terminating or [
                ph for ph in boundaries
                if re.search(r"[.!?][\"\']?$", ph["text"].strip())
            ] or boundaries
            best = None
            for ph in pool:
                dist = abs(ph["end"] - t)
                if best is None or dist < best[0]:
                    best = (dist, ph["end"])

            # Accept a boundary much further away before accepting a broken
            # ending. A clip that runs long and closes a thought beats one that
            # ends mid-clause at the perfect length - the viewer remembers the
            # ending. TED-style speech regularly runs 40s+ per sentence, so a
            # tight window here means every clip ends mid-clause.
            if best and best[0] <= 40.0:
                return best[1]

        # Nearest boundary, no hard tolerance.
        #
        # The tolerance used to stop the window drifting from the retention peak.
        # But landing on a clean sentence start is worth a few seconds of drift:
        # "up anytime a deadline gets too close" reads as a fragment and kills the
        # hook, while "Now, of course, I said yes" does not. Sentence integrity
        # first, proximity second.
        best = None
        for ph in boundaries:
            edge = ph["start"] if prefer == "start" else ph["end"]
            dist = abs(edge - t)
            if best is None or dist < best[0]:
                best = (dist, edge)
        if best and best[0] <= 25.0:
            return best[1]
        return t

    def make(start: float, end: float, origin: str, peak: dict | None) -> dict:
        """Snap edges to phrase boundaries (falling back to word boundaries), then score."""
        if end <= start:
            return {}

        # Order matters and this is the fix for clips that ended mid-clause.
        #
        # 1. Clamp the raw window to the ceiling FIRST, on raw times.
        # 2. Then snap the edges to sentence boundaries.
        #
        # The old order did it backwards: snap first, then chop back to max_d.
        # That chop ignored sentences entirely, so any clip whose snapped end
        # exceeded the ceiling got sliced mid-clause - which is exactly the
        # "throughout the" / "what's the" endings this replaces.
        if end - start > max_d:
            end = start + max_d

        start = snap_to_phrase(start, "start")
        end = snap_to_phrase(end, "end")

        # snapping may have pushed past the ceiling; re-clamp, but only to a
        # sentence boundary so we never slice mid-thought
        if end - start > max_d:
            overshoot = end - start - max_d
            candidates_end = [
                b["end"] for b in boundaries
                if b["end"] <= start + max_d and b["end"] > start
            ]
            if candidates_end:
                end = max(candidates_end)
            else:
                end = start + max_d

        window = [w for w in words if w["end"] > start and w["start"] < end]
        if not window:
            return {}
        snapped_start = window[0]["start"]
        snapped_end = window[-1]["end"]
        dur = snapped_end - snapped_start

        # the floor is a floor. A clip meaningfully under --min is not a
        # candidate at that length; it is a different, shorter clip the user did
        # not ask for. Reject rather than quietly returning something too thin.
        if dur < min_d:
            return {}

        win_phrases = _window_phrases(phrases, snapped_start, snapped_end)
        first = win_phrases[0]["text"] if win_phrases else ""

        h = score_hook(first, win_phrases[1:6])
        r = score_retention(heatmap, snapped_start, snapped_end)
        f = score_fit(
            dur, snapped_start, snapped_end, total, platform,
            min_d=min_d, max_d=max_d, ideal_d=options.get("ideal_duration"),
        )
        comp = composite(h["score"], r["score"], f["score"], has_heatmap)

        closing = (win_phrases[-1]["text"] if win_phrases else "").strip().lower()
        closing_bare = closing.strip(" .!?\"'")
        weak_close = closing_bare in WEAK_CLOSERS or len(closing_bare.split()) <= 3

        return {
            "start": round(snapped_start, 2),
            "end": round(snapped_end, 2),
            "duration": round(dur, 2),
            "start_hms": fmt_time(snapped_start),
            "end_hms": fmt_time(snapped_end),
            "origin": origin,
            "peak_time": peak["time"] if peak else None,
            "first_line": first,
            # the closing line must be the sentence the clip ends on, not an
            # arbitrary slice of words - a trailing fragment reads as a broken
            # clip even when the timestamps are correct
            "last_line": _closing_line(boundaries, snapped_end) or (
                " ".join(w["text"] for w in window[-12:]) if window else ""
            ),
            "text": " ".join(p["text"] for p in win_phrases),
            "scores": {
                "hook": h["score"],
                "retention": r["score"],
                "fit": f["score"],
                "composite": comp,
            },
            "evidence": {
                "hook": h["reasons"],
                "retention": r["reasons"],
                "fit": f["reasons"],
                "signals": h["signals"],
                "retention_stats": r["stats"],
                "weak_close": weak_close,
            },
        }

    # --- A. windows around retention peaks (before / centred / after)
    for peak in peaks:
        t = peak["time"]
        for offset, origin in ((-0.15, "peak-lead"), (0.0, "peak-centred"), (0.25, "peak-tail")):
            start = max(0.0, t - options["ideal_duration"] * (0.5 + offset))
            end = min(total, start + options["ideal_duration"])
            c = make(start, end, origin, peak)
            if c:
                c["evidence"]["peak"] = peak
                candidates.append(c)

    # --- B. windows opened by a strong transcript line
    #
    # Thresholds relax in steps rather than failing to zero. A music video or a
    # dry technical talk will not clear 55, but it may still have usable moments
    # at 40. We record which threshold actually fired so the report can say how
    # confident the shortlist is.
    ideal = options["ideal_duration"]
    threshold_used = None
    for threshold in (55.0, 45.0, 38.0, 32.0):
        found_this_pass = 0
        for p in phrases:
            line = _norm(p["text"])
            if len(line.split()) < 5:
                continue
            if _is_lyric(line):
                continue
            quick = score_hook(p["text"], [])
            if quick["score"] < threshold:
                continue
            found_this_pass += 1
            for dur in (min_d, ideal, max_d):
                end = min(total, p["start"] + dur)
                c = make(p["start"], end, "hook-line", None)
                if c:
                    candidates.append(c)
        if candidates:
            threshold_used = threshold
            break
    if threshold_used is not None:
        log(f"  hook-line threshold used: {threshold_used:.0f}")

    # --- dedupe overlapping windows, keep the strongest
    candidates.sort(key=lambda c: c["scores"]["composite"], reverse=True)
    kept: list[dict] = []
    for c in candidates:
        overlap = False
        for k in kept:
            inter = min(c["end"], k["end"]) - max(c["start"], k["start"])
            if inter > 0.6 * min(c["duration"], k["duration"]):
                overlap = True
                break
        if not overlap:
            kept.append(c)

    for i, c in enumerate(kept, 1):
        c["id"] = f"c{i:02d}"
        c["slug"] = slugify(c["first_line"] or f"clip-{i}")
        c["tiktok_title"] = suggest_title(c)

    log(f"  candidates: {len(candidates)} generated -> {len(kept)} after overlap dedupe")
    return kept


def suggest_title(candidate: dict) -> str:
    """A placeholder title the agent must rewrite. Marked so it is never shipped as-is."""
    line = candidate.get("first_line", "").strip()
    line = re.sub(r"\s+", " ", line)
    if len(line) > 70:
        line = line[:67].rsplit(" ", 1)[0] + "..."
    return f"{line}  # [AGENT: rewrite as a TikTok hook, max 60 chars]"
