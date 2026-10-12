"""sfx_fetch.py - Build a local CC0 sound-effect library for the Remotion project.

Searches Openverse (no API key needed, CC0 only, sourced from Freesound), picks the
best-fitting files per category, trims leading silence, peak-normalizes them with
FFmpeg, and writes them into <remotion-dir>/public/sfx/<category>/.

Outputs:
    public/sfx/<category>/<category>-NN.wav
    public/sfx/sfx-manifest.json   (title, creator, license, source page per file)
    src/sfx-library.json           (category -> [staticFile paths], used by <SfxLayer>)

Usage:
    python hook-radar/scripts/sfx_fetch.py                      # all categories, 3 each
    python hook-radar/scripts/sfx_fetch.py --only whoosh hit    # refresh some categories
    python hook-radar/scripts/sfx_fetch.py --per-category 4 --force
    python hook-radar/scripts/sfx_fetch.py --only hit --force --exclude-id <openverse-id>  # replace a rejected sound
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import fail, log, read_json, run_cmd, which, write_json  # noqa: E402
from export_remotion import find_remotion_dir  # noqa: E402

API = "https://api.openverse.org/v1/audio/"
USER_AGENT = "hook-radar-sfx-fetch/1.0"

# category -> search queries, accepted duration window (seconds), max kept length (seconds)
CATEGORIES: dict[str, dict] = {
    "impact": {"queries": ["cinematic impact", "boom impact", "trailer hit"], "min": 0.4, "max": 4.0, "cap": 2.5},
    "hit": {"queries": ["punch hit", "hit stinger", "snare hit"], "min": 0.1, "max": 1.5, "cap": 1.2},
    "whoosh": {"queries": ["whoosh", "swoosh", "woosh transition"], "min": 0.25, "max": 2.0, "cap": 1.5},
    "swipe": {"queries": ["swipe", "swish", "fast swish"], "min": 0.1, "max": 1.0, "cap": 0.8},
    "pop": {"queries": ["pop", "bubble pop", "cork pop"], "min": 0.03, "max": 0.8, "cap": 0.6},
    "riser": {"queries": ["riser", "uplifter", "tension riser"], "min": 1.5, "max": 6.0, "cap": 4.0},
    "ding": {"queries": ["ding", "bell ding", "notification ding"], "min": 0.2, "max": 3.0, "cap": 2.0},
    "glitch": {"queries": ["glitch", "digital glitch", "glitch transition"], "min": 0.15, "max": 2.0, "cap": 1.5},
    "record-scratch": {"queries": ["record scratch", "vinyl scratch"], "min": 0.3, "max": 3.0, "cap": 2.0},
    "shutter": {"queries": ["camera shutter", "shutter click"], "min": 0.05, "max": 1.5, "cap": 1.0},
}

# Titles containing these are rarely usable as a one-shot editing SFX.
REJECT_WORDS = re.compile(
    r"\b(loop|music|song|ambien|ambience|atmos|voice|vocal|speech|talk|pack|collection|field ?recording|beat)\b",
    re.IGNORECASE,
)


def parse_args():
    ap = argparse.ArgumentParser(prog="sfx_fetch", description="Download a CC0 SFX library into the Remotion project.")
    ap.add_argument("--remotion-dir", default=None, help="Remotion project dir (auto-detected if omitted)")
    ap.add_argument("--per-category", type=int, default=3, help="Variants per category (default: 3)")
    ap.add_argument("--only", nargs="*", default=None, help=f"Only these categories: {', '.join(CATEGORIES)}")
    ap.add_argument("--exclude-id", nargs="*", default=[], help="Openverse IDs to never pick again")
    ap.add_argument("--force", action="store_true", help="Replace existing files in the selected categories")
    return ap.parse_args()


def search(query: str, page: int) -> list[dict]:
    params = urllib.parse.urlencode({"q": query, "license": "cc0", "page_size": 20, "page": page, "mature": "false"})
    req = urllib.request.Request(f"{API}?{params}", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp).get("results", [])
    except Exception as exc:  # network / rate-limit: keep going with other queries
        log(f"  [search failed] '{query}' p{page}: {exc}")
        return []


def score(item: dict, query: str, spec: dict) -> float | None:
    """Return a ranking score, or None if the item is unusable."""
    if item.get("license") != "cc0" or item.get("mature"):
        return None
    dur = (item.get("duration") or 0) / 1000
    if not (spec["min"] <= dur <= spec["max"]):
        return None
    title = item.get("title") or ""
    if REJECT_WORDS.search(title):
        return None
    words = query.lower().split()
    tags = {t.get("name", "").lower() for t in item.get("tags") or []}
    s = 0.0
    s += 2.0 * sum(w in title.lower() for w in words)
    s += 1.0 * sum(w in tags for w in words)
    s -= 0.3 * dur  # shorter one-shots are punchier
    return s


def pick(category: str, spec: dict, count: int, excluded: set[str]) -> list[dict]:
    ranked: dict[str, tuple[float, dict]] = {}
    for query in spec["queries"]:
        for page in (1, 2):
            for item in search(query, page):
                if item["id"] in excluded:
                    continue
                s = score(item, query, spec)
                if s is not None and (item["id"] not in ranked or ranked[item["id"]][0] < s):
                    ranked[item["id"]] = (s, item)
    chosen: list[dict] = []
    creators: set[str] = set()
    # first pass: one per creator for variety, second pass fills the rest
    for unique in (True, False):
        for _, item in sorted(ranked.values(), key=lambda x: -x[0]):
            if len(chosen) >= count:
                break
            if item in chosen or (unique and item.get("creator") in creators):
                continue
            chosen.append(item)
            creators.add(item.get("creator"))
    return chosen


def download(url: str, dest: Path) -> bool:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            dest.write_bytes(resp.read())
        return dest.stat().st_size > 0
    except Exception as exc:
        log(f"  [download failed] {url}: {exc}")
        return False


def process(src: Path, dest: Path, cap: float) -> bool:
    """Trim leading silence (so cues land on the frame), cap length, fade tail, peak-normalize to -1 dBFS."""
    trim = (
        "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.01,"
        f"atrim=0:{cap},afade=t=out:st={max(cap - 0.05, 0)}:d=0.05"
    )
    probe = run_cmd(["ffmpeg", "-hide_banner", "-i", str(src), "-af", f"{trim},volumedetect", "-f", "null", "-"], quiet=True)
    m = re.search(r"max_volume:\s*(-?[\d.]+) dB", probe.stderr or "")
    gain = (-1.0 - float(m.group(1))) if m else 0.0
    proc = run_cmd([
        "ffmpeg", "-hide_banner", "-y", "-i", str(src),
        "-af", f"{trim},volume={gain:.2f}dB",
        "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(dest),
    ])
    return proc.returncode == 0 and dest.exists() and dest.stat().st_size > 1000


def main():
    args = parse_args()
    if not which("ffmpeg"):
        fail("ffmpeg not found on PATH.")
    remotion_dir = find_remotion_dir(args.remotion_dir)
    if not remotion_dir:
        fail("Remotion project not found. Pass --remotion-dir.")

    selected = args.only or list(CATEGORIES)
    unknown = [c for c in selected if c not in CATEGORIES]
    if unknown:
        fail(f"Unknown categories: {unknown}. Available: {list(CATEGORIES)}")

    sfx_root = remotion_dir / "public" / "sfx"
    manifest_path = sfx_root / "sfx-manifest.json"
    manifest: dict = read_json(manifest_path) if manifest_path.exists() else {"source": "Openverse (CC0)", "categories": {}}
    # rejected sounds are remembered so a later --force never picks them again
    excluded = set(manifest.get("excluded_ids", [])) | set(args.exclude_id)
    manifest["excluded_ids"] = sorted(excluded)

    with tempfile.TemporaryDirectory() as tmp:
        for category in selected:
            spec = CATEGORIES[category]
            cat_dir = sfx_root / category
            existing = manifest["categories"].get(category, [])
            if existing and not args.force:
                log(f"[{category}] already has {len(existing)} files, skipping (use --force to replace)")
                continue
            log(f"[{category}] searching...")
            items = pick(category, spec, args.per_category, excluded)
            if not items:
                log(f"[{category}] no usable results")
                continue
            if cat_dir.exists():
                for old in cat_dir.glob("*.wav"):
                    old.unlink()
            cat_dir.mkdir(parents=True, exist_ok=True)
            entries = []
            for i, item in enumerate(items, 1):
                raw = Path(tmp) / f"{item['id']}.{item.get('filetype') or 'mp3'}"
                dest = cat_dir / f"{category}-{i:02d}.wav"
                if not (download(item["url"], raw) and process(raw, dest, spec["cap"])):
                    continue
                entries.append({
                    "file": f"sfx/{category}/{dest.name}",
                    "title": item.get("title"),
                    "creator": item.get("creator"),
                    "license": "CC0 1.0",
                    "source_page": item.get("foreign_landing_url"),
                    "original_url": item.get("url"),
                    "original_duration_s": round((item.get("duration") or 0) / 1000, 2),
                    "openverse_id": item["id"],
                })
                log(f"  + {dest.name}  <- \"{item.get('title')}\" by {item.get('creator')}")
            manifest["categories"][category] = entries

    write_json(manifest_path, manifest)
    library = {cat: [e["file"] for e in entries] for cat, entries in manifest["categories"].items()}
    write_json(remotion_dir / "src" / "sfx-library.json", library)
    print(json.dumps({"status": "ready", "sfx_dir": str(sfx_root), "counts": {k: len(v) for k, v in library.items()}}, indent=2))


if __name__ == "__main__":
    main()
