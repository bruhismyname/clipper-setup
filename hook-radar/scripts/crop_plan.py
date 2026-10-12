"""crop_plan.py - Prepare the per-shot crop plan for Style B "Fullbleed Speaker".

Style B fills the 9:16 frame with one person at a time, so every camera shot in the clip
needs a horizontal face position (centerX, 0 = left edge of the 16:9 source, 1 = right edge).
This script does the mechanical part without any AI: ffmpeg's `scene` filter finds the
camera cuts, then each shot's middle frame is drawn with a 0.1-step X grid into one contact
sheet. You (or the agent) read the sheet and fill in centerX / zoom / who per segment.
A wide two-shot can be split into several segments by hand to cut between speakers.

Outputs (in <run>/remotion/<candidate>/):
    crop-plan.json   segments in clip seconds: start, end, centerX, centerY, zoom, who
    crop-sheet.jpg   one tile per segment: "#N  start-end s" + X grid 0.1 ... 0.9

Usage:
    python hook-radar/scripts/crop_plan.py 2acQX8r0oyY --candidate b01 --start 3:10 --end 4:25
    # edit crop-plan.json, then
    python hook-radar/scripts/export_remotion.py 2acQX8r0oyY --style fullbleed --candidate b01 --start 3:10 --end 4:25 ...
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import fail, fmt_time, log, parse_time, read_json, which, write_json  # noqa: E402
from export_remotion import find_source_video, resolve_run_dir  # noqa: E402

FONT = Path("C:/Windows/Fonts/arialbd.ttf")


def parse_args():
    ap = argparse.ArgumentParser(prog="crop_plan", description="Detect camera cuts and build the Style B crop plan template.")
    ap.add_argument("target", help="YouTube URL, 11-char video ID, or path to runs/<id>")
    ap.add_argument("--candidate", default="b01", help="Clip id, same as export_remotion --candidate (default: b01)")
    ap.add_argument("--start", required=True, help="Clip start in the source (seconds or MM:SS)")
    ap.add_argument("--end", required=True, help="Clip end in the source (seconds or MM:SS)")
    ap.add_argument("--threshold", type=float, default=0.3, help="ffmpeg scene-change threshold (default: 0.3)")
    ap.add_argument("--min-shot", type=float, default=0.3, help="Merge mid-clip shots shorter than this many seconds (default: 0.3)")
    ap.add_argument("--source-video", help="Path to the episode MP4 (default: <run>/source.mp4)")
    ap.add_argument("--out-dir", help="Output directory (default: <run>/remotion/<candidate>)")
    ap.add_argument("--force", action="store_true", help="Overwrite an existing crop-plan.json (loses manual edits)")
    return ap.parse_args()


def detect_cuts(src: Path, start: float, dur: float, threshold: float) -> list[float]:
    """Seconds (relative to the clip start) where the camera shot changes."""
    cmd = ["ffmpeg", "-hide_banner", "-ss", f"{start:.3f}", "-i", str(src), "-t", f"{dur:.3f}", "-an",
           "-vf", f"scale=320:-2,select='gt(scene,{threshold})',showinfo", "-f", "null", "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        fail(f"ffmpeg scene detection failed: {proc.stderr[-300:]}")
    return sorted({round(float(t), 3) for t in re.findall(r"pts_time:([\d.]+)", proc.stderr)})


def build_segments(cuts: list[float], dur: float, min_shot: float) -> list[dict]:
    bounds = [0.0] + [c for c in cuts if 0 < c < dur] + [round(dur, 3)]
    pairs = list(zip(bounds, bounds[1:]))
    segs: list[list[float]] = []
    for i, (a, b) in enumerate(pairs):
        # Flash frames / dissolves inside the clip fold into the previous shot. A short shot at the
        # very start or end is a real shot cut off by the clip window, so it keeps its own crop.
        is_edge = i == 0 or i == len(pairs) - 1
        if segs and b - a < min_shot and not is_edge:
            segs[-1][1] = b
        else:
            segs.append([a, b])
    return [{"start": round(a, 3), "end": round(b, 3), "centerX": 0.5, "centerY": 0.5, "zoom": 1.0, "who": ""}
            for a, b in segs]


def grid_filter(label: str) -> str:
    vf = "scale=480:-2,drawgrid=w=iw/10:h=ih:t=1:c=yellow@0.55"
    if FONT.exists():
        font = "C\\:/Windows/Fonts/arialbd.ttf"
        for i in range(1, 10):
            vf += (f",drawtext=fontfile='{font}':text='0.{i}':x=w*{i / 10:.1f}-tw/2:y=h-th-6:"
                   "fontsize=15:fontcolor=yellow:box=1:boxcolor=black@0.6:boxborderw=2")
        vf += (f",drawtext=fontfile='{font}':text='{label}':x=8:y=8:fontsize=20:fontcolor=white:"
               "box=1:boxcolor=black@0.7:boxborderw=4")
    return vf


def build_sheet(src: Path, start: float, segments: list[dict], sheet: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        for i, seg in enumerate(segments, 1):
            mid = start + (seg["start"] + seg["end"]) / 2
            label = f"#{i}  {seg['start']:.1f}-{seg['end']:.1f}s"
            out = Path(tmp) / f"seg_{i:03d}.jpg"
            proc = subprocess.run(["ffmpeg", "-hide_banner", "-y", "-ss", f"{mid:.3f}", "-i", str(src), "-frames:v", "1",
                                   "-vf", grid_filter(label), "-q:v", "3", str(out)],
                                  capture_output=True, text=True, encoding="utf-8", errors="replace")
            if proc.returncode != 0 or not out.exists():
                fail(f"Could not grab the frame for segment {i}: {proc.stderr[-300:]}")
        cols = 4
        rows = (len(segments) + cols - 1) // cols
        proc = subprocess.run(["ffmpeg", "-hide_banner", "-y", "-framerate", "1", "-i", str(Path(tmp) / "seg_%03d.jpg"),
                               "-vf", f"tile={cols}x{rows}:padding=6:color=black", "-frames:v", "1", "-q:v", "3", str(sheet)],
                              capture_output=True, text=True, encoding="utf-8", errors="replace")
        if proc.returncode != 0:
            fail(f"Could not build the contact sheet: {proc.stderr[-300:]}")


def main():
    args = parse_args()
    if not which("ffmpeg"):
        fail("ffmpeg not found on PATH.")
    rd = resolve_run_dir(args.target)
    src = find_source_video(rd, args.source_video)
    start, end = parse_time(args.start), parse_time(args.end)
    if end <= start:
        fail("--end must be after --start.")
    dur = round(end - start, 3)

    out_dir = Path(args.out_dir) if args.out_dir else rd / "remotion" / args.candidate
    out_dir.mkdir(parents=True, exist_ok=True)
    plan_path = out_dir / "crop-plan.json"
    if plan_path.exists() and not args.force:
        old = read_json(plan_path)
        fail(f"{plan_path} already exists (window {old.get('start')}-{old.get('end')}). It may hold manual crop "
             "positions; pass --force to rebuild it.")

    log(f"Detecting camera cuts in {fmt_time(start)} -> {fmt_time(end)} ({dur:.1f}s)...")
    cuts = detect_cuts(src, start, dur, args.threshold)
    segments = build_segments(cuts, dur, args.min_shot)
    sheet = out_dir / "crop-sheet.jpg"
    build_sheet(src, start, segments, sheet)

    write_json(plan_path, {
        "candidate": args.candidate,
        "source": str(src),
        "start": start,
        "end": end,
        "note": "Fill centerX (face position 0-1 from the grid), zoom (1-1.25) and who (host/guest/other) per "
                "segment. Split a wide shot into several segments to cut between speakers. Times are clip seconds.",
        "segments": segments,
    })
    print(json.dumps({"status": "ready", "segments": len(segments), "cuts": len(cuts),
                      "crop_plan": str(plan_path), "contact_sheet": str(sheet)}, indent=2))


if __name__ == "__main__":
    main()
