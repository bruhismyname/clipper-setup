---
name: hook-radar
description: >
  Find the hook moments in a YouTube video that will actually perform on TikTok.
  Give it a YouTube URL; it pulls the audience-retention heatmap ("Most Replayed"),
  a word-level transcript, and the video metadata, then returns ranked clip
  candidates with exact start/end timestamps, hook scores, and the evidence behind
  every score. Use when the user says "find hooks in this video", "which parts of
  this video will go viral", "clip this YouTube link for TikTok", "where should I
  cut this", "find the best moments", or drops a YouTube link and asks what is
  worth clipping. Works in any agent harness that can run a shell command.
license: MIT
version: 1.0.0
---

# Hook Radar

Turn one YouTube link into a ranked shortlist of TikTok hook moments with the
timestamps, the reasoning, and the audience data behind every pick.

## Core Principle

**Do not guess what will hold attention. YouTube already measured it.**

Every video with enough views carries a "Most Replayed" curve: the audience's
own rewatch data, second by second. That curve is an objective signal for
what survives a swipe. Most clipper tools ignore it and ask an LLM to guess from
the transcript alone.

Hook Radar reads both, and treats their disagreement as information:

| Signal | Source | Tells you |
|---|---|---|
| **Retention peaks** | YouTube heatmap | Where viewers actually rewatched |
| **Hook lines** | Word-level transcript | Where a line opens a curiosity loop |
| **Format fit** | Duration + position | Whether it survives TikTok's rules |

Where the two agree, you have a candidate clip. Where the retention peak has a weak opening
line, the clip needs a re-cut rather than a discard.

## Hard Rules

These are correctness requirements:

1. **Never cut inside a word.** Snap every clip edge to a word boundary from the transcript.
2. **Never invent a timestamp.** Every timecode comes from `words.json`. If it is not there, say so.
3. **A clip must stand alone.** If it needs 30 seconds of setup to make sense, it is not a clip. Flag it and move on.
4. **Never ship a context trap.** Lines like "as I said earlier", "this slide", "like we discussed" mean the clip is meaningless outside the source.
5. **The score is a shortlist, not a verdict.** Your judgement overrides it. State when you disagree and why.
6. **Never fabricate the heatmap.** If a video has no Most-Replayed data, state "no retention data" instead of presenting transcript-only scoring as audience-validated.
7. **Report what you cannot know.** You cannot watch or hear the video. State when a judgement requires visual or audio verification.
8. **One clip, one idea.** Two hooks in one clip should be separated into two clips.

## Setup Check (first run only)

Run this command to verify dependencies:

```bash
python3 -c "import sys; print(sys.version)"           # need 3.10+
ffmpeg -version | head -1                              # optional, only for whisper fallback
python3 -c "import yt_dlp; print('yt-dlp', yt_dlp.version.__version__)" 2>/dev/null || echo "yt-dlp: NOT INSTALLED (fallback fetcher will be used)"
```

- Missing `yt-dlp` is not fatal; `fetch.py` falls back to the YouTube innertube API using the standard library.
- `faster-whisper` is only needed for videos with no caption track.

## Usage

```bash
python3 scripts/run.py "<youtube-url>"
```

Common variations:

```bash
# top 5 only, tighter clips
python3 scripts/run.py "<url>" --top 5 --min 12 --max 30

# force a fresh fetch (ignore cache)
python3 scripts/run.py "<url>" --force

# rescore an existing run without refetching
python3 scripts/run.py "<url>" --from-meta workspace/runs/<id>/meta.json

# machine-readable only (for piping into other tools)
python3 scripts/run.py "<url>" --json
```

Runs write to `workspace/runs/<video_id>/`. Override the location with
`--workspace <dir>` or `HOOK_RADAR_WORKSPACE=<dir>`.

## Output Structure

```
workspace/runs/<video_id>/
├── meta.json              # raw fetch: metadata, heatmap, caption tracks
├── heatmap.json           # detected retention peaks + baseline
├── words.json             # word-level transcript (source of truth for cuts)
├── phrases.json           # phrase-level transcript
├── transcript_packed.md   # reading view: one line per phrase with [start-end]
├── candidates.json        # ranked clips with scores + evidence (machine-readable)
└── report.md              # summary report
```

## The Pipeline

```
fetch -> heatmap -> transcript -> score -> [AGENT: judge + write hooks]
```

1. **Fetch**: metadata, Most-Replayed curve, caption track. yt-dlp if present, innertube otherwise.
2. **Heatmap**: smooth the curve, find local maxima, rank peaks by intensity.
3. **Transcript**: word-level timestamps (json3 preferred, faster-whisper fallback) normalized to `{start, end, text}`.
4. **Score**: generate candidates from retention peaks and transcript signals, snap edges to word boundaries, dedupe overlaps, score each candidate.
5. **Agent Evaluation**: Read `candidates.json`, apply `references/scoring-rubric.md`, and write the final hooks.

## Evaluation Workflow

The script produces a shortlist; your task is to evaluate and refine:

1. **Read `candidates.json`.** Then read `transcript_packed.md` around top candidates. Do not judge a clip from its first line alone.
2. **Re-rank on judgement.** The composite score weighs hook 0.45, retention 0.35, and fit 0.20 when heatmap data exists. Override when content has strong conversational or topical relevance that heuristics cannot detect.
3. **Reject context traps.** Any candidate whose meaning changes when removed from the source must be flagged or rejected.
4. **Write the hook for each selected clip**, following `references/hook-formulas.md`:
   - `hook_0_3s`: exact words spoken in the first three seconds
   - `on_screen_text`: maximum 7 words on the opening frame
   - `caption`: post caption
   - `hashtags`: 3-5 relevant hashtags
   - `why_it_works`: technical mechanism explanation
5. **Flag risks.** Note anything needing visual verification, claims that may be ambiguous out of context, or segments under 8 seconds.

## Output Schema

Present final results using this JSON schema:

```json
{
  "video": {"title": "...", "channel": "...", "duration_s": 0, "heatmap_available": true},
  "clips": [
    {
      "rank": 1,
      "id": "c01",
      "start": 0.0,
      "end": 0.0,
      "start_hms": "0:00.00",
      "duration_s": 0,
      "hook_0_3s": "...",
      "on_screen_text": "...",
      "caption": "...",
      "hashtags": ["#..."],
      "why_it_works": "...",
      "evidence": {
        "retention_delta": "+0.00 vs baseline",
        "hook_signals": ["..."],
        "first_line": "..."
      },
      "confidence": "high|medium|low",
      "flags": ["needs visual check", "context-dependent"]
    }
  ],
  "rejected": [{"id": "c07", "reason": "..."}],
  "caveats": ["no heatmap data for this video", "..."]
}
```

## Reference Files

| File | Read when |
|---|---|
| `references/hook-formulas.md` | Writing the hook text for a clip |
| `references/tiktok-signals.md` | Evaluating platform suitability |
| `references/scoring-rubric.md` | Re-ranking candidates based on rubrics |
| `references/heatmap-guide.md` | Interpreting retention curve data |

## Limitations

- **No heatmap = weaker ranking.** Videos without sufficient view count lack a Most-Replayed curve. Scores rely on transcript heuristics.
- **Transcript vs delivery.** Timing, expression, and delivery cannot be measured from text alone. Flag when delivery is critical.
- **Purely visual or music moments are invisible.** Dialogue-free segments produce empty transcripts.
- **Rendering clips**: To cut and render with dynamic captions, pass candidate timestamps to `scripts/export_remotion.py` and render via Remotion.

## Failure Modes and Recovery

| Symptom | Cause | Action |
|---|---|---|
| `Could not read video metadata` | Private, region-locked, or age-gated video | Ask user for a public URL |
| `No word-level captions ... no audio to transcribe` | No caption track and no downloaded video | Re-run with `--keep-source` or install `faster-whisper` |
| `no retention heatmap available` | Video too new or low views | Continue with transcript analysis and note caveat |
| Very few candidates | Sparse speech or heavy background music | Note that source format may not fit dialogue extraction |
| Captions in wrong language | Multi-language track selected | Re-run with `--language <code>` |
