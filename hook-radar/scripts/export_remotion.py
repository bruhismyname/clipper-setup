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
    fail,
    fmt_time,
    log,
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
    ap.add_argument("--html-type", choices=["browser", "tweet", "search", "notification", ""], default="", help="HTML Motion mockup type")
    ap.add_argument("--html-url", default="", help="URL for browser mockup")
    ap.add_argument("--html-headline", default="", help="Headline for browser mockup")
    ap.add_argument("--html-tweet", default="", help="Tweet text for X mockup")
    ap.add_argument("--html-author", default="", help="Author name for X mockup")
    ap.add_argument("--text-slam", default="", help="Kinetic typography slam text")
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


def find_source_video(rd: Path, explicit_path: str | None) -> Path | None:
    if explicit_path:
        ep = Path(explicit_path)
        if ep.exists():
            return ep
        log(f"Warning: Specified source video '{explicit_path}' does not exist.")

    # Check run_dir / source.mp4
    if (rd / "source.mp4").exists():
        return rd / "source.mp4"

    # Check root project directory for matching .mp4
    root = Path(__file__).resolve().parent.parent.parent
    for mp4 in root.glob("*.mp4"):
        return mp4

    return None


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


def find_remotion_dir(explicit: str | None = None) -> Path | None:
    if explicit:
        p = Path(explicit)
        if p.exists() and (p / "package.json").exists():
            return p
    env_dir = os.environ.get("REMOTION_DIR")
    if env_dir:
        p = Path(env_dir)
        if p.exists() and (p / "package.json").exists():
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
    has_video = False
    if source_mp4:
        log(f"Using source video: {source_mp4}")
        has_video = slice_video(source_mp4, start_sec, end_sec, clip_mp4)
    else:
        log("No source video found. You can place source.mp4 in run_dir or pass --source-video.")

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
    if args.broll_src:
        props["brolls"] = [
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
        ]

    # Add HTML Motion mockup if requested
    if args.html_type:
        item = {
            "type": args.html_type,
            "startFrame": int(args.fps * 2.0),
            "endFrame": int(args.fps * 5.5),
        }
        if args.html_type == "browser":
            item["url"] = args.html_url or "https://news.google.com"
            item["headline"] = args.html_headline or headline
            item["sourceName"] = "BREAKING NEWS"
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
                "startFrame": int(args.fps * 3.0),
                "endFrame": int(args.fps * 4.8),
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

    # Add Outro CTA banner (Campaign Compliance)
    if not args.no_outro:
        props["outroCta"] = {
            "enabled": True,
            "channelName": args.outro_channel,
            "seriesName": args.outro_series,
            "ctaText": args.outro_cta,
        }

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
        "props_path": str(props_path.resolve()),
        "clip_path": str(clip_mp4.resolve()) if has_video else None,
        "remotion_ready": True,
        "total_words": len(slice_words),
    }, indent=2))


if __name__ == "__main__":
    main()
