"""export_remotion.py - Bridge from hook-radar candidates to Remotion video & props.

Usage:
    python hook-radar/scripts/export_remotion.py DZtGxNs9AVg --candidate c01 --headline "10M ARR DALAM 60 HARI"
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (  # noqa: E402
    emoji_filename,
    fail,
    fmt_time,
    log,
    parse_time,
    read_json,
    run_cmd,
    run_dir,
    video_id_from_url,
    which,
    write_json,
)


def parse_args():
    ap = argparse.ArgumentParser(
        prog="export_remotion",
        description="Slice video clip and prepare Remotion props from hook-radar output.",
    )
    ap.add_argument("target", help="YouTube URL, 11-char video ID, or path to runs/<id>")
    ap.add_argument("--candidate", default="c01", help="Candidate ID to export (default: c01)")
    ap.add_argument("--start", default="", help="Curated clip start in the source (seconds or MM:SS); overrides the candidate window")
    ap.add_argument("--end", default="", help="Curated clip end in the source (seconds or MM:SS); use with --start")
    ap.add_argument("--headline", default="", help="Hook banner headline for upper frame")
    ap.add_argument("--source-video", help="Path to local source video MP4 (optional)")
    ap.add_argument("--out-dir", help="Output directory (default: <run-dir>/remotion/<candidate_id>)")
    ap.add_argument("--fps", type=int, default=30, help="Video framerate (default: 30)")
    # MG-Styles arguments
    ap.add_argument("--stat-number", type=float, default=None, help="Numeric value for animated stat counter")
    ap.add_argument("--stat-prefix", default="", help="Prefix e.g. $")
    ap.add_argument("--stat-suffix", default="", help="Suffix e.g. M ARR")
    ap.add_argument("--stat-label", default="", help="Stat label e.g. IN 60 DAYS")
    ap.add_argument("--sticker-text", default="", help="Text for Paperclip sticker badge")
    ap.add_argument("--sticker-sub", default="CASE STUDY", help="Subtext for sticker badge")
    # Professional Clipper Layer arguments
    ap.add_argument("--speaker-name", default="", help="Speaker name for Talking Head spotlight badge")
    ap.add_argument("--speaker-tag", default="", help="Speaker title/tag e.g. HOST or EXPERT")
    ap.add_argument("--broll-src", default="", help="Path or filename to B-roll video/image")
    ap.add_argument("--broll-caption", default="", help="Caption for B-roll card")
    ap.add_argument("--broll-start", type=float, default=6.0, help="Start second for B-roll")
    ap.add_argument("--broll-duration", type=float, default=3.0, help="Duration in seconds for B-roll")
    ap.add_argument(
        "--broll-from", action="append", default=[], metavar="START-END[@AT]",
        help="Cut a B-roll from the episode source video, e.g. 754-757 or 12:34-12:37@6 "
             "(source range, optional @ = second inside the clip; default --broll-start). Repeatable.",
    )
    ap.add_argument(
        "--broll-asset", action="append", default=[], metavar="FILE@AT[+DUR]",
        help="Place a file from broll_fetch.py, e.g. broll/new-york-night-01.mp4@12 or broll/times-square-01.jpg@20+2.5 "
             "(path inside my-video/public, @ = second inside the clip, + = seconds on screen; default 3 video / 2.5 photo). Repeatable.",
    )
    ap.add_argument("--html-type", choices=["browser", "tweet", "search", "notification", ""], default="", help="HTML Motion mockup type")
    ap.add_argument("--html-url", default="", help="URL for browser mockup")
    ap.add_argument("--html-headline", default="", help="Headline for browser mockup")
    ap.add_argument("--html-tweet", default="", help="Tweet text for X mockup")
    ap.add_argument("--html-author", default="", help="Author name for X mockup")
    ap.add_argument("--html-screenshot", default="", help="Real page capture from web_capture.py (e.g. screens/x.png) shown inside the browser mockup")
    ap.add_argument("--html-at", type=float, default=2.0, help="Second inside the clip where the HTML mockup appears (default: 2)")
    ap.add_argument("--html-duration", type=float, default=3.5, help="Seconds the HTML mockup stays on screen (default: 3.5)")
    ap.add_argument("--text-slam", default="", help="Kinetic typography slam text")
    ap.add_argument("--text-slam-at", type=float, default=3.0, help="Second inside the clip where the text slam hits (default: 3)")
    ap.add_argument("--text-slam-duration", type=float, default=1.8, help="Seconds the text slam stays (default: 1.8)")
    # v4.0.0 Universal Safe Zone & Advanced Motion Stack
    ap.add_argument("--attention-badge", default="🔥 MUST WATCH", help="Attention trigger text for frames 0-90 (detik 0-3)")
    ap.add_argument("--show-safe-zone", action="store_true", help="Display visual safe zone guide boundary overlay")
    ap.add_argument("--no-hook-anim", action="store_true", help="Disable hook impact flash & camera slam")
    ap.add_argument("--no-body-anim", action="store_true", help="Disable retention progress bar & camera drift")
    ap.add_argument("--no-fx", action="store_true", help="Disable vignette & chromatic aberration")
    # Gozmotion / Usman Explains Minimal Editorial Aesthetic
    ap.add_argument("--doc-tag", default="ARCHIVE // VIRAL DOSSIER", help="Monospace technical dossier tag")
    ap.add_argument("--no-grid", action="store_true", help="Disable blueprint gridline overlay")
    ap.add_argument("--no-annotations", action="store_true", help="Disable viewfinder corner brackets & technical annotations")
    # Campaign Compliance Outro CTA
    ap.add_argument("--outro-channel", default="LYRICAL LEMONADE TV", help="Channel name for Outro CTA banner")
    ap.add_argument("--outro-series", default="NO COMFORT", help="Series/playlist name for Outro CTA banner")
    ap.add_argument("--outro-cta", default="WATCH FULL EPISODE ON YOUTUBE", help="Action text for Outro CTA banner")
    ap.add_argument("--no-outro", action="store_true", help="Disable Outro CTA banner")
    # Sound design
    ap.add_argument("--no-sfx", action="store_true", help="Disable auto-cued sound effects")
    ap.add_argument("--sfx-volume", type=float, default=None, help="SFX master volume 0-1 (default: 0.35 card, 0.25 fullbleed)")
    # v5.0.0 Style B "Fullbleed Speaker" (ATM of @dailyyskchaos), rendered by the FullBleedClip composition
    ap.add_argument("--style", choices=["card", "fullbleed"], default="card",
                    help="card = Style A editorial card (ContentRewardVideo); fullbleed = Style B (FullBleedClip)")
    ap.add_argument("--crop-plan", default="", help="Style B crop plan from crop_plan.py (default: <out-dir>/crop-plan.json)")
    ap.add_argument("--caption-y", type=int, default=880, help="Style B one-word caption center Y in px (default: 880 = 46%%)")
    ap.add_argument(
        "--overlay", action="append", default=[], metavar="FILE@AT[+DUR]",
        help="Style B keyword overlay from overlay_fetch.py, e.g. overlays/avocado-01.jpg@1.2+1.5 or emoji:🤔@0.4+1.2 "
             "(@ = second inside the clip, + = seconds on screen, default 1.5). Repeatable.",
    )
    ap.add_argument("--remotion-dir", default=None, help="Path to Remotion project directory (auto-detected if omitted)")
    return ap.parse_args()


def resolve_run_dir(target_str: str) -> Path:
    p = Path(target_str)
    if p.is_dir() and (p / "candidates.json").exists():
        return p
    vid = video_id_from_url(target_str)
    rd = run_dir(vid)
    if not (rd / "candidates.json").exists():
        fail(f"Candidates file not found in {rd}. Run hook-radar/scripts/run.py first.")
    return rd


def find_source_video(rd: Path, explicit_path: str | None) -> Path:
    """Only --source-video or <run_dir>/source.mp4. Never guess another file: a stray
    .mp4 elsewhere would silently slice the wrong episode."""
    if explicit_path:
        ep = Path(explicit_path)
        if not ep.is_file():
            fail(f"--source-video '{explicit_path}' does not exist.")
        return ep

    src = rd / "source.mp4"
    if src.is_file():
        return src

    fail(
        f"Source video not found: {src}\n"
        f"  Download it:  python hook-radar/scripts/run.py <URL> --download-video\n"
        f"  or point to an existing file:  --source-video <path-to-episode.mp4>"
    )


def slice_video(src: Path, start: float, end: float, out_mp4: Path) -> bool:
    ffmpeg = which("ffmpeg")
    if not ffmpeg:
        log("Warning: ffmpeg not found in PATH. Skipping video slicing.")
        return False

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    duration = end - start
    cmd = [
        ffmpeg,
        "-y",
        "-ss", f"{start:.3f}",
        "-i", str(src),
        "-t", f"{duration:.3f}",
        "-r", "30",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-g", "1",
        "-keyint_min", "1",
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-b:a", "192k",
        "-avoid_negative_ts", "make_zero",
        str(out_mp4),
    ]
    log(f"Slicing clip with ffmpeg: {start:.2f}s -> {end:.2f}s ({duration:.2f}s)")
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        log(f"ffmpeg error: {proc.stderr[:300]}")
        return False
    return True


def parse_broll_from(spec: str) -> tuple[float, float, float | None]:
    """'754-757' | '12:34-12:37@6' -> (src_start, src_end, at_or_None)."""
    rng, _, at = spec.partition("@")
    a, sep, b = rng.partition("-")
    if not sep:
        fail(f"--broll-from '{spec}': expected START-END, e.g. 754-757 or 12:34-12:37@6")
    try:
        start, end = parse_time(a), parse_time(b)
        at_sec = parse_time(at) if at else None
    except ValueError:
        fail(f"--broll-from '{spec}': could not parse the times")
    if end <= start:
        fail(f"--broll-from '{spec}': END must be after START")
    return start, end, at_sec


def cut_episode_brolls(specs: list[str], source_mp4: Path | None, clip_duration: float,
                       default_at: float, cand_id: str, out_dir: Path, fps: int) -> list[dict]:
    """Slice B-roll cutaways from the episode itself (zero licensing risk, same footage)."""
    if not specs:
        return []
    if not source_mp4:
        fail("--broll-from needs the episode source video. Pass --source-video or place source.mp4 in the run dir.")
    ffmpeg = which("ffmpeg")
    if not ffmpeg:
        fail("--broll-from needs ffmpeg on PATH.")

    items = []
    for i, spec in enumerate(specs, 1):
        src_start, src_end, at = parse_broll_from(spec)
        if at is None:
            if i > 1:
                fail(f"--broll-from '{spec}': add @AT (second inside the clip) for every B-roll after the first")
            at = default_at
        dur = src_end - src_start
        if dur > 4.0:
            log(f"Warning: B-roll {i} is {dur:.1f}s; keep cutaways at 1.5-3s so the host stays on screen.")
        if at + dur > clip_duration - 3.0:
            log(f"Warning: B-roll {i} ({at:.1f}s + {dur:.1f}s) runs into the outro CTA (last 3s of the clip).")
        out_mp4 = out_dir / f"{cand_id}-broll-{i:02d}.mp4"
        # Video only (B-roll is muted in Remotion), scaled for the 840px card, intra-frame for exact seeking
        cmd = [
            ffmpeg, "-y", "-ss", f"{src_start:.3f}", "-i", str(source_mp4), "-t", f"{dur:.3f}",
            "-an", "-vf", "scale=-2:'min(1080,ih)'", "-r", str(fps),
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-g", "1", "-keyint_min", "1",
            "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out_mp4),
        ]
        log(f"Cutting B-roll {i} from episode: {fmt_time(src_start)} -> {fmt_time(src_end)} ({dur:.2f}s) at clip {at:.2f}s")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0 or not out_mp4.exists():
            fail(f"ffmpeg failed cutting B-roll {i}: {proc.stderr[-300:]}")
        items.append({"path": out_mp4, "at": at, "duration": dur, "src_start": src_start})
    total = sum(it["duration"] for it in items)
    if total > 0.5 * clip_duration:
        log(f"Warning: B-roll covers {total:.1f}s of {clip_duration:.1f}s; campaign needs the host on screen >=20%.")
    return items


def parse_broll_asset(spec: str) -> tuple[str, float, float | None]:
    """'broll/x.mp4@12' | 'broll/x.jpg@20+2.5' -> (public_path, at, duration_or_None)."""
    path, sep, timing = spec.rpartition("@")
    if not sep or not path:
        fail(f"--broll-asset '{spec}': expected FILE@AT, e.g. broll/new-york-night-01.mp4@12")
    at_text, plus, dur_text = timing.partition("+")
    try:
        return path.replace("\\", "/"), parse_time(at_text), (float(dur_text) if plus else None)
    except ValueError:
        fail(f"--broll-asset '{spec}': could not parse the timing")


def stock_brolls(specs: list[str], remotion_dir: Path | None, clip_duration: float, fps: int,
                 caption: str) -> list[dict]:
    """B-roll items for files downloaded by broll_fetch.py, credited from its license manifest."""
    if not specs:
        return []
    if not remotion_dir:
        fail("--broll-asset needs the Remotion project (pass --remotion-dir).")
    public = remotion_dir / "public"
    manifest_path = public / "broll" / "broll-manifest.json"
    manifest = {e["file"]: e for e in read_json(manifest_path)["files"]} if manifest_path.exists() else {}
    items = []
    for spec in specs:
        path, at, dur = parse_broll_asset(spec)
        path = path.split("public/")[-1]
        if not (public / path).exists():
            fail(f"--broll-asset: {public / path} not found. Download it first with broll_fetch.py.")
        is_video = path.lower().endswith((".mp4", ".mov", ".webm"))
        dur = dur if dur is not None else (3.0 if is_video else 2.5)
        if at + dur > clip_duration - 3.0:
            log(f"Warning: B-roll {path} ({at:.1f}s + {dur:.1f}s) runs into the outro CTA (last 3s of the clip).")
        entry = manifest.get(path, {})
        if not entry:
            log(f"Warning: {path} is not in broll-manifest.json; check its license yourself.")
        items.append({
            "src": path,
            "type": "video" if is_video else "image",
            "mode": "card",
            "startFrame": int(round(at * fps)),
            "endFrame": int(round((at + dur) * fps)),
            "caption": caption or (entry.get("query") or "").upper() or "B-ROLL",
            "sourceCredit": entry.get("credit", ""),
            "kenBurns": True,
        })
    return items


def smart_title(text: str) -> str:
    """'LYRICAL LEMONADE TV' -> 'Lyrical Lemonade TV' for the caption-styled Style B CTA."""
    if text != text.upper():
        return text
    return " ".join(w if len(w) <= 2 else w.capitalize() for w in text.split())


def load_crop_plan(path: Path, start: float, end: float, duration: float, fps: int) -> tuple[list[dict], float]:
    """crop-plan.json (clip seconds) -> speakerCrop segments in frames, plus the host share."""
    if not path.exists():
        fail(f"Style B needs a crop plan: {path} not found. Build it with:\n"
             f"  python hook-radar/scripts/crop_plan.py <VIDEO_ID> --candidate <ID> --start {start} --end {end}")
    plan = read_json(path)
    if abs(float(plan.get("start", start)) - start) > 0.05 or abs(float(plan.get("end", end)) - end) > 0.05:
        fail(f"{path} was made for {plan.get('start')}-{plan.get('end')}, not {start}-{end}. "
             "Rebuild it (crop_plan.py --force) or fix the window, otherwise the crops land on the wrong shots.")
    segs = sorted(plan.get("segments", []), key=lambda s: float(s["start"]))
    if not segs:
        fail(f"{path} has no segments.")
    total = int(round(duration * fps))
    out = []
    for i, s in enumerate(segs):
        cx = float(s.get("centerX", 0.5))
        if not 0 <= cx <= 1:
            fail(f"{path} segment {i + 1}: centerX must be 0-1 (got {cx}).")
        a = int(round(float(s["start"]) * fps))
        b = int(round(float(segs[i + 1]["start"]) * fps)) if i + 1 < len(segs) else total
        if out and a != out[-1]["to"]:
            log(f"Warning: crop plan gap/overlap at {float(s['start']):.2f}s; segment {i + 1} now starts where the previous ends.")
            a = out[-1]["to"]
        out.append({"from": a if i else 0, "to": max(a + 1, b), "centerX": round(cx, 4),
                    "centerY": float(s.get("centerY", 0.5)), "zoom": max(1.0, float(s.get("zoom", 1.0))),
                    "who": s.get("who", "")})
    if all(s["centerX"] == 0.5 for s in out):
        log("Warning: every crop segment is still centerX 0.5 (template value). Fill the crop plan from crop-sheet.jpg.")
    host = sum(s["to"] - s["from"] for s in out if s["who"] == "host") / max(1, total)
    if not any(s["who"] for s in out):
        log("Warning: no segment is tagged who=host/guest; the host >=20% rule cannot be checked.")
    elif host < 0.2:
        log(f"Warning: host is framed only {host:.0%} of the clip; the campaign needs >=20%.")
    return out, host


def parse_overlays(specs: list[str], remotion_dir: Path | None, fps: int, duration: float) -> list[dict]:
    """--overlay FILE@AT[+DUR] / emoji:X@AT[+DUR] -> KeywordOverlayItem dicts (credit from overlays-manifest.json)."""
    if not specs:
        return []
    if not remotion_dir:
        fail("--overlay needs the Remotion project (pass --remotion-dir).")
    public = remotion_dir / "public"
    manifest_path = public / "overlays" / "overlays-manifest.json"
    manifest = {e["file"]: e for e in read_json(manifest_path)["files"]} if manifest_path.exists() else {}
    items = []
    for spec in specs:
        target, sep, timing = spec.rpartition("@")
        if not sep or not target:
            fail(f"--overlay '{spec}': expected FILE@AT[+DUR], e.g. overlays/avocado-01.jpg@1.2+1.5 or emoji:🤔@0.4")
        at_text, plus, dur_text = timing.partition("+")
        try:
            at, dur = parse_time(at_text), (float(dur_text) if plus else 1.5)
        except ValueError:
            fail(f"--overlay '{spec}': could not parse the timing")
        if target.startswith("emoji:"):
            path, kind = f"overlays/emoji/{emoji_filename(target[len('emoji:'):])}", "emoji"
            hint = f"overlay_fetch.py --emoji {target[len('emoji:'):]}"
        else:
            path = target.replace("\\", "/").split("public/")[-1]
            kind = "png" if path.lower().endswith(".png") else "photo"
            hint = "overlay_fetch.py"
        if not (public / path).exists():
            fail(f"--overlay: {public / path} not found. Fetch it first with {hint}.")
        if at + dur > duration:
            fail(f"--overlay '{spec}' ends after the clip ({duration:.1f}s).")
        entry = manifest.get(path, {})
        if not entry and kind != "emoji":
            log(f"Warning: {path} is not in overlays-manifest.json; check its license yourself.")
        items.append({"src": path, "from": int(round(at * fps)), "duration": max(1, int(round(dur * fps))),
                      "kind": kind, "credit": entry.get("credit", "")})
    return sorted(items, key=lambda o: o["from"])


def check_fullbleed_pacing(overlays: list[dict], brolls: list[dict], duration: float, fps: int, cta_s: float) -> None:
    """Style B anti low-effort rules (workflow.md §5.5): plain cuts + captions get rejected by the campaign."""
    if not 45 <= duration <= 90:
        log(f"Warning: Style B clips should run 45-90s (this one is {duration:.1f}s).")
    if not overlays:
        log("WARNING: no --overlay given. Crop + captions alone counts as 'plain cuts with auto-captions' "
            "(rules.md §3). Do not publish this clip without keyword overlays.")
        return
    body_end = (duration - cta_s) * fps
    starts = [o["from"] for o in overlays if o["from"] < body_end]
    if starts and starts[0] > 2 * fps:
        log(f"Warning: first overlay at {starts[0] / fps:.1f}s; Style B wants one within the first 2s.")
    for a, b in zip([0] + starts, starts + [int(body_end)]):
        if b - a > 6 * fps:
            log(f"Warning: no overlay between {a / fps:.1f}s and {b / fps:.1f}s (aim for one every 3-5s).")
    covered = sum(o["duration"] for o in overlays) / max(1, duration * fps)
    if covered > 0.45:
        log(f"Warning: overlays cover {covered:.0%} of the clip (max 45%).")
    for o in overlays:
        for b in brolls:
            if o["from"] < b["endFrame"] and b["startFrame"] < o["from"] + o["duration"]:
                log(f"Warning: overlay {o['src']} at {o['from'] / fps:.1f}s overlaps a full-screen B-roll.")
    if len(brolls) > 2 or any(b["endFrame"] - b["startFrame"] > 2 * fps + 1 for b in brolls):
        log("Warning: Style B allows at most 2 full-screen B-rolls of <=2s each.")


def find_remotion_dir(explicit: str | None = None) -> Path | None:
    # An explicit target that is wrong must stop the run: falling back would overwrite
    # the active remotion-props.json of another project.
    for label, value in (("--remotion-dir", explicit), ("REMOTION_DIR", os.environ.get("REMOTION_DIR"))):
        if value:
            p = Path(value)
            if not (p / "package.json").is_file():
                fail(f"{label} '{value}' is not a Remotion project (no package.json).")
            return p
    template_dir = Path(__file__).resolve().parent.parent.parent / "remotion-template"
    if template_dir.exists() and (template_dir / "package.json").exists():
        return template_dir
    local_dir = Path("C:/Users/Lenovo/my-video")
    if local_dir.exists() and (local_dir / "package.json").exists():
        return local_dir
    return None


def main():
    args = parse_args()
    rd = resolve_run_dir(args.target)
    cands_data = read_json(rd / "candidates.json")
    words_data = read_json(rd / "words.json")

    candidates = cands_data.get("candidates", [])
    if args.start or args.end:
        # Curated window (e.g. trimmed to skip dead air); --candidate becomes its id
        if not (args.start and args.end):
            fail("--start and --end must be given together.")
        s, e = parse_time(args.start), parse_time(args.end)
        if e <= s:
            fail("--end must be after --start.")
        first = next((w["text"] for w in words_data if float(w["start"]) >= s - 0.05), "")
        cand = {"id": args.candidate, "start": s, "end": e, "duration": round(e - s, 3),
                "start_hms": fmt_time(s), "end_hms": fmt_time(e), "first_line": first, "scores": {}}
    else:
        cand = next((c for c in candidates if c.get("id") == args.candidate), None)
    if not cand:
        cand_ids = [c.get("id") for c in candidates]
        fail(f"Candidate '{args.candidate}' not found. Available: {cand_ids}")

    start_sec = float(cand["start"])
    end_sec = float(cand["end"])
    duration_sec = float(cand["duration"])

    out_dir = Path(args.out_dir) if args.out_dir else rd / "remotion" / args.candidate
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Slice words for this segment (clean speaker markers like >>)
    slice_words = []
    for w in words_data:
        w_start = float(w["start"])
        w_end = float(w["end"])
        if w_start >= (start_sec - 0.1) and w_end <= (end_sec + 0.15):
            clean_text = w["text"].replace(">>", "").strip()
            if not clean_text:
                continue
            rel_start = max(0.0, round(w_start - start_sec, 3))
            rel_end = max(rel_start + 0.05, round(w_end - start_sec, 3))
            slice_words.append({
                "text": clean_text,
                "start": rel_start,
                "end": rel_end,
                "startMs": int(rel_start * 1000),
                "endMs": int(rel_end * 1000),
                "startFrame": int(round(rel_start * args.fps)),
                "endFrame": int(round(rel_end * args.fps)),
            })

    # 2. Slice video if available
    source_mp4 = find_source_video(rd, args.source_video)
    clip_mp4 = out_dir / "clip.mp4"
    log(f"Using source video: {source_mp4}")
    has_video = slice_video(source_mp4, start_sec, end_sec, clip_mp4)
    if not has_video:
        fail("Could not slice the clip from the source video (see the ffmpeg message above).")

    # 3. Create Remotion props
    headline = args.headline.strip()
    if not headline:
        headline = cand.get("first_line", "").strip()
        if len(headline) > 60:
            headline = headline[:57] + "..."

    # Detect Remotion project (clipper-setup/remotion-template or C:/Users/Lenovo/my-video)
    remotion_dir = find_remotion_dir(args.remotion_dir)
    public_file_name = f"{cand.get('id')}-clip.mp4" if has_video else "clip.mp4"
    if remotion_dir and (remotion_dir / "package.json").exists() and has_video:
        public_dir = remotion_dir / "public"
        public_dir.mkdir(parents=True, exist_ok=True)
        dest_public = public_dir / public_file_name
        shutil.copy2(clip_mp4, dest_public)
        log(f"Synced clip to Remotion public dir: {dest_public}")
        # also copy as default clip.mp4 for convenience
        shutil.copy2(clip_mp4, public_dir / "clip.mp4")

    props = {
        "candidateId": cand.get("id"),
        "videoSrc": public_file_name if has_video else "",
        "hookHeadline": headline,
        "durationInSeconds": round(duration_sec, 3),
        "durationInFrames": int(round(duration_sec * args.fps)),
        "fps": args.fps,
        "width": 1080,
        "height": 1920,
        "start": start_sec,
        "end": end_sec,
        "startHms": cand.get("start_hms", fmt_time(start_sec)),
        "endHms": cand.get("end_hms", fmt_time(end_sec)),
        "scores": cand.get("scores", {}),
        "captions": slice_words,
        "enableGrain": not args.no_fx,
        "showSafeZone": args.show_safe_zone,
        "hookAnimation": {
            "enabled": not args.no_hook_anim,
            "impactFlash": not args.no_hook_anim,
            "cameraSlam": not args.no_hook_anim,
            "attentionBadge": {
                "text": args.attention_badge,
                "color": "#FF3B30",
            } if args.attention_badge else None,
        },
        "bodyAnimation": {
            "enabled": not args.no_body_anim,
            "retentionProgressBar": not args.no_body_anim,
            "ambientCameraDrift": not args.no_body_anim,
            "floatingParticles": not args.no_body_anim,
        },
        "advancedVisualEffects": {
            "enabled": not args.no_fx,
            "vignette": not args.no_fx,
            "chromaticAberration": not args.no_fx,
            "lightLeak": not args.no_fx,
            "filmGrain": not args.no_fx,
        },
        "editorialGrid": not args.no_grid,
        "technicalAnnotations": not args.no_annotations,
        "docTag": args.doc_tag,
    }

    # Add sticker if requested
    if args.sticker_text:
        props["stickers"] = [
            {
                "text": args.sticker_text.upper(),
                "subtext": args.sticker_sub.upper(),
                "startFrame": int(args.fps * 0.5),
                "endFrame": int(args.fps * 4.5),
                "position": "top-right",
            }
        ]

    # Add Talking Head spotlight badge if requested
    if args.speaker_name:
        props["talkingHead"] = {
            "enabled": True,
            "speakerName": args.speaker_name,
            "speakerTag": args.speaker_tag or "HOST",
            "position": "bottom-left",
            "glowColor": "#FFE600",
            "dynamicPunchZoom": True,
        }

    # Add B-Roll cutaways if requested
    brolls = []
    if args.broll_src:
        brolls.append(
            {
                "src": args.broll_src,
                "type": "video" if args.broll_src.endswith((".mp4", ".mov", ".webm")) else "image",
                "mode": "card",
                "startFrame": int(args.broll_start * args.fps),
                "endFrame": int((args.broll_start + args.broll_duration) * args.fps),
                "caption": args.broll_caption or "ARCHIVE FOOTAGE",
                "sourceCredit": "EVIDENCE",
                "kenBurns": True,
            }
        )
    for it in cut_episode_brolls(args.broll_from, source_mp4, duration_sec, args.broll_start,
                                 cand.get("id"), out_dir, args.fps):
        if remotion_dir and (remotion_dir / "package.json").exists():
            shutil.copy2(it["path"], remotion_dir / "public" / it["path"].name)
        brolls.append({
            "src": it["path"].name,
            "type": "video",
            "mode": "card",
            "startFrame": int(round(it["at"] * args.fps)),
            "endFrame": int(round((it["at"] + it["duration"]) * args.fps)),
            "caption": args.broll_caption or "FROM THE EPISODE",
            "sourceCredit": f"@ {fmt_time(it['src_start'])}",
            "kenBurns": True,
        })
    brolls += stock_brolls(args.broll_asset, remotion_dir, duration_sec, args.fps, args.broll_caption)

    if args.style == "fullbleed":
        props = build_fullbleed_props(args, cand, rd, out_dir, clip_mp4, public_file_name, remotion_dir,
                                      slice_words, brolls, start_sec, end_sec, duration_sec)
        write_props(props, out_dir, remotion_dir, cand, duration_sec, clip_mp4, slice_words, "FullBleedClip")
        return

    if brolls:
        props["brolls"] = sorted(brolls, key=lambda b: b["startFrame"])

    # Add HTML Motion mockup if requested
    if args.html_type:
        item = {
            "type": args.html_type,
            "startFrame": int(round(args.fps * args.html_at)),
            "endFrame": int(round(args.fps * (args.html_at + args.html_duration))),
        }
        if args.html_type == "browser":
            item["url"] = args.html_url or "https://news.google.com"
            item["headline"] = args.html_headline or headline
            item["sourceName"] = "BREAKING NEWS"
            if args.html_screenshot:
                shot = args.html_screenshot.replace("\\", "/").split("public/")[-1]
                shots_manifest = (remotion_dir / "public" / "screens" / "screens-manifest.json") if remotion_dir else None
                shots = {e["file"]: e for e in read_json(shots_manifest)["files"]} if shots_manifest and shots_manifest.exists() else {}
                if remotion_dir and not (remotion_dir / "public" / shot).exists():
                    fail(f"--html-screenshot: {shot} not found in my-video/public. Capture it first with web_capture.py.")
                meta = shots.get(shot, {})
                item["screenshot"] = shot
                if meta.get("width"):
                    item["screenshotAspect"] = round(meta["height"] / meta["width"], 4)
                if not args.html_url and meta.get("url"):
                    item["url"] = meta["url"]
        elif args.html_screenshot:
            log("Warning: --html-screenshot only works with --html-type browser; ignored.")
        elif args.html_type == "tweet":
            item["tweetText"] = args.html_tweet or headline
            item["authorName"] = args.html_author or "Viral Feed"
            item["authorHandle"] = "@viralfeed"
            item["likesCount"] = "34.5K"
            item["retweetsCount"] = "8.2K"
        elif args.html_type == "search":
            item["searchQuery"] = headline.lower()
        props["htmlMotion"] = [item]

    # Add Kinetic Text Motion slam if requested
    if args.text_slam:
        props["textMotion"] = [
            {
                "text": args.text_slam.upper(),
                "startFrame": int(round(args.fps * args.text_slam_at)),
                "endFrame": int(round(args.fps * (args.text_slam_at + args.text_slam_duration))),
                "color": "#FF3B30",
                "position": "center",
            }
        ]

    # Add Stat Callout if requested
    if args.stat_number is not None:
        props["statCallout"] = {
            "targetNumber": args.stat_number,
            "prefix": args.stat_prefix,
            "suffix": args.stat_suffix,
            "label": args.stat_label or "KEY METRIC",
            "startFrame": int(args.fps * 1.0),
            "endFrame": int(args.fps * 5.0),
        }

    # Outro CTA banner (Campaign Compliance). Always written: when omitted, the
    # component falls back to its default (enabled), so --no-outro must be explicit.
    props["outroCta"] = {
        "enabled": not args.no_outro,
        "channelName": args.outro_channel,
        "seriesName": args.outro_series,
        "ctaText": args.outro_cta,
    }

    # Auto-cued SFX from the CC0 library (public/sfx, built by sfx_fetch.py)
    props["sfx"] = {
        "enabled": not args.no_sfx,
        "auto": True,
        "masterVolume": args.sfx_volume if args.sfx_volume is not None else 0.35,
        "minGapFrames": 8,
    }

    write_props(props, out_dir, remotion_dir, cand, duration_sec, clip_mp4, slice_words, "ContentRewardVideo")


def build_fullbleed_props(args, cand: dict, rd: Path, out_dir: Path, clip_mp4: Path, public_file_name: str,
                          remotion_dir: Path | None, slice_words: list[dict], brolls: list[dict],
                          start_sec: float, end_sec: float, duration_sec: float) -> dict:
    """Props for the Style B FullBleedClip composition (spec: workflow.md §5.4)."""
    fps = args.fps
    plan_path = Path(args.crop_plan) if args.crop_plan else out_dir / "crop-plan.json"
    speaker_crop, host = load_crop_plan(plan_path, start_sec, end_sec, duration_sec, fps)
    overlays = parse_overlays(args.overlay, remotion_dir, fps, duration_sec)
    cta_frames = int(round(2.5 * fps))
    for b in brolls:
        b["mode"] = "fullscreen"
    brolls = sorted(brolls, key=lambda b: b["startFrame"])
    check_fullbleed_pacing(overlays, brolls, duration_sec, fps, 2.5)

    probe = run_cmd(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                     "-of", "csv=p=0", str(clip_mp4)], quiet=True)
    try:
        src_w, src_h = (int(v) for v in probe.stdout.strip().split(",")[:2])
    except ValueError:
        fail(f"ffprobe could not read the size of {clip_mp4}")
    if src_h < 1080:
        log(f"Warning: source is {src_w}x{src_h}; the 9:16 crop is upscaled {1920 / src_h:.1f}x and will look soft. Use a 1080p source.")

    default_cta = "WATCH FULL EPISODE ON YOUTUBE"
    log(f"Style B: {len(speaker_crop)} crop segments (host {host:.0%}), {len(overlays)} overlays, {len(brolls)} full-screen B-rolls.")
    return {
        "style": "fullbleed",
        "candidateId": cand.get("id"),
        "videoSrc": public_file_name,
        "sourceWidth": src_w,
        "sourceHeight": src_h,
        "durationInSeconds": round(duration_sec, 3),
        "durationInFrames": int(round(duration_sec * fps)),
        "fps": fps,
        "width": 1080,
        "height": 1920,
        "start": start_sec,
        "end": end_sec,
        "startHms": cand.get("start_hms", fmt_time(start_sec)),
        "endHms": cand.get("end_hms", fmt_time(end_sec)),
        "captions": slice_words,
        "speakerCrop": speaker_crop,
        "overlays": overlays,
        "brolls": brolls,
        "caption": {"enabled": True, "centerY": args.caption_y, "fontSize": 78},
        "outroCta": {
            "enabled": not args.no_outro,
            "style": "minimal",
            "channelName": smart_title(args.outro_channel),
            "seriesName": smart_title(args.outro_series),
            "ctaText": "watch the full episode on YouTube 👇" if args.outro_cta == default_cta else args.outro_cta,
            "durationInFrames": cta_frames,
        },
        "sfx": {
            "enabled": not args.no_sfx,
            "auto": True,
            "masterVolume": args.sfx_volume if args.sfx_volume is not None else 0.25,
            "minGapFrames": 8,
        },
        "showSafeZone": args.show_safe_zone,
    }


def write_props(props: dict, out_dir: Path, remotion_dir: Path | None, cand: dict, duration_sec: float,
                clip_mp4: Path, slice_words: list[dict], composition: str) -> None:
    props_path = out_dir / "remotion-props.json"
    write_json(props_path, props)
    log(f"Remotion props written to: {props_path}")

    if remotion_dir and remotion_dir.exists() and (remotion_dir / "package.json").exists():
        remotion_props_copy = remotion_dir / "remotion-props.json"
        write_json(remotion_props_copy, props)
        log(f"Synced props to Remotion root: {remotion_props_copy}")

    print(json.dumps({
        "status": "ready",
        "candidate": cand.get("id"),
        "duration": duration_sec,
        "composition": composition,
        "props_path": str(props_path.resolve()),
        "clip_path": str(clip_mp4.resolve()),
        "remotion_ready": True,
        "total_words": len(slice_words),
    }, indent=2))


if __name__ == "__main__":
    main()
