"""Triage many videos at once: metadata + retention curve strength.

Runs yt-dlp in parallel (metadata only, no video, no captions) and reports the
numbers needed to decide which sources are worth a full analysis:

  - duration, views
  - how many retention peaks the curve actually has
  - peak strength (max intensity above baseline)
  - whether captions exist

The point is to spend the expensive analysis only on videos that carry signal.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PY = sys.executable
LINKS = Path("hook-radar/workspace/triage/links.txt")
OUT = Path("hook-radar/workspace/triage/triage.json")


def fetch(vid: str) -> dict:
    cmd = [
        PY, "-m", "yt_dlp",
        "--dump-single-json", "--skip-download", "--no-warnings",
        "--no-playlist", f"https://www.youtube.com/watch?v={vid}",
    ]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=180)
        if p.returncode != 0 or not p.stdout.strip():
            err = (p.stderr or "")[-200:]
            return {"id": vid, "error": err or "no output"}
        info = json.loads(p.stdout)
    except Exception as exc:
        return {"id": vid, "error": str(exc)[:200]}

    hm = info.get("heatmap") or []
    vals = [float(h.get("value") or 0) for h in hm]
    mean = sum(vals) / len(vals) if vals else 0.0
    mx = max(vals) if vals else 0.0

    # count points that stand clearly above the video's own baseline
    strong = sum(1 for v in vals if v > mean * 1.6 and v > 0.45) if vals else 0

    subs = info.get("subtitles") or {}
    auto = info.get("automatic_captions") or {}

    return {
        "id": vid,
        "title": info.get("title"),
        "channel": info.get("uploader") or info.get("channel"),
        "duration": info.get("duration"),
        "views": info.get("view_count"),
        "likes": info.get("like_count"),
        "heatmap_points": len(hm),
        "baseline_mean": round(mean, 4),
        "peak_max": round(mx, 4),
        "strong_points": strong,
        "has_manual_caption": bool(subs),
        "caption_langs": list(subs.keys())[:4],
        "has_auto_caption": "en" in auto or "en-US" in auto,
        "upload_date": info.get("upload_date"),
    }


def main() -> None:
    pairs = []
    for line in LINKS.read_text(encoding="utf-8").splitlines():
        if "|" not in line:
            continue
        name, vid = line.split("|", 1)
        pairs.append((name.strip(), vid.strip()))

    print(f"triaging {len(pairs)} videos ...", file=sys.stderr)
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda p: fetch(p[1]), pairs))

    rows = []
    for (name, vid), r in zip(pairs, results):
        r["name"] = name
        rows.append(r)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")

    ok = [r for r in rows if not r.get("error")]
    err = [r for r in rows if r.get("error")]
    print(f"ok: {len(ok)}  failed: {len(err)}", file=sys.stderr)
    for r in err:
        print(f"  FAIL {r['name'][:28]:30} {r['error'][:70]}", file=sys.stderr)


if __name__ == "__main__":
    main()
