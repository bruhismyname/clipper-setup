"""broll_fetch.py - Search & download licensed stock B-roll into the Remotion project.

Sources (no AI-generated media):
    video  -> Pixabay Videos API (PIXABAY_API_KEY in .env; Pixabay Content License, no attribution needed)
    photo  -> Openverse Images (no key; CC0 / CC BY / CC BY-SA from Wikimedia, Flickr, ...;
              NC and ND licenses are excluded, attribution is stored and shown as the B-roll credit)

Every file is normalized for the 840px B-roll card: videos are trimmed to --max-seconds,
muted, 720p intra-frame (exact seeking in Remotion); photos become JPG <= 1600px wide.

Outputs:
    <remotion>/public/broll/<name>-NN.mp4|jpg
    <remotion>/public/broll/broll-manifest.json   (source page, creator, license, credit per file)

Usage:
    python hook-radar/scripts/broll_fetch.py "new york night"                     # 3 Pixabay videos
    python hook-radar/scripts/broll_fetch.py "times square" --kind photo --count 2
    python hook-radar/scripts/broll_fetch.py "money counting" --name cash --max-seconds 3

Then place one in a clip:
    export_remotion.py <VIDEO_ID> --candidate c01 --broll-asset broll/new-york-night-01.mp4@12
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import env_key, fail, log, read_json, run_cmd, slugify, which, write_json  # noqa: E402
from export_remotion import find_remotion_dir  # noqa: E402

USER_AGENT = "hook-radar-broll-fetch/1.0"
# Stock libraries now host generated media; the campaign rejects anything AI-made
AI_MARKERS = ("ai generated", "ai-generated", "ai art", "artificial intelligence", "generative", "midjourney",
              "stable diffusion", "dall-e", "dalle", "neural network art")
PIXABAY_VIDEOS = "https://pixabay.com/api/videos/"
OPENVERSE_IMAGES = "https://api.openverse.org/v1/images/"


def parse_args():
    ap = argparse.ArgumentParser(prog="broll_fetch", description="Download licensed stock B-roll into the Remotion project.")
    ap.add_argument("query", help="Search keywords, e.g. 'new york night'")
    ap.add_argument("--kind", choices=["video", "photo"], default="video", help="video = Pixabay, photo = Openverse (default: video)")
    ap.add_argument("--count", type=int, default=3, help="How many files to download (default: 3)")
    ap.add_argument("--name", default="", help="File name prefix (default: slug of the query)")
    ap.add_argument("--max-seconds", type=float, default=4.0, help="Trim videos to this length (default: 4)")
    ap.add_argument("--min-duration", type=float, default=3.0, help="Skip videos shorter than this (default: 3)")
    ap.add_argument("--loose", action="store_true",
                    help="Also accept results whose tags only contain the query words separately (less relevant)")
    ap.add_argument("--remotion-dir", default=None, help="Remotion project dir (auto-detected if omitted)")
    return ap.parse_args()


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def relevance(query: str, tags: list[str], title: str = "", loose: bool = False) -> int | None:
    """3 = a tag equals the query, 2 = a tag/title contains it, 1 = every word tagged separately (only with
    loose=True: 'green' + 'bean' also matches a chicken dish); None = AI-made or off-topic."""
    tags = [t.strip().lower() for t in tags if t.strip()]
    text = " ".join(tags + [title.lower()])
    if any(m in text for m in AI_MARKERS):
        return None
    phrase = query.lower().strip()
    variants = {phrase, phrase.rstrip("s"), f"{phrase}s"}
    if variants & set(tags):
        return 3
    if any(v in t for v in variants for t in tags + [title.lower()]):
        return 2
    if not loose:
        return None
    words = phrase.split()
    tag_words = set(" ".join(tags).replace("-", " ").split()) | set(title.lower().split())
    if all(w in tag_words or w.rstrip("s") in tag_words or f"{w}s" in tag_words for w in words):
        return 1
    return None


def download(url: str, dest: Path) -> bool:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            dest.write_bytes(resp.read())
        return dest.stat().st_size > 0
    except Exception as exc:
        log(f"  [download failed] {url[:90]}: {exc}")
        return False


# ---------------------------------------------------------------- search

def search_pixabay_videos(query: str, min_duration: float, known: set[str], loose: bool) -> list[dict]:
    key = env_key("PIXABAY_API_KEY")
    if not key:
        fail("PIXABAY_API_KEY not found. Add it to D:/Project/clonee/.env")
    params = urllib.parse.urlencode({"key": key, "q": query, "per_page": 50, "safesearch": "true", "order": "popular"})
    try:
        hits = get_json(f"{PIXABAY_VIDEOS}?{params}").get("hits", [])
    except Exception as exc:
        fail(f"Pixabay search failed: {exc}")
    results = []
    for h in hits:
        uid = f"pixabay:{h['id']}"
        if uid in known or h.get("duration", 0) < min_duration:
            continue
        rank = relevance(query, (h.get("tags") or "").split(","), loose=loose)
        if rank is None:
            continue
        # medium is 1280x720 for landscape footage: enough for the 840px card, light to download
        rendition = next((h["videos"][k] for k in ("medium", "large", "small") if h["videos"].get(k, {}).get("url")), None)
        if not rendition or rendition["width"] < rendition["height"]:
            continue
        results.append({
            "uid": uid,
            "url": rendition["url"],
            "ext": "mp4",
            "source": "pixabay",
            "source_page": h.get("pageURL"),
            "creator": h.get("user"),
            "license": "Pixabay Content License",
            "attribution": None,
            "credit": f"PIXABAY / {h.get('user', '').upper()}",
            "tags": h.get("tags"),
            "rank": rank,
        })
    return sorted(results, key=lambda r: -r["rank"])


def search_openverse_photos(query: str, known: set[str], loose: bool) -> list[dict]:
    params = urllib.parse.urlencode({
        "q": query, "license_type": "commercial,modification", "mature": "false",
        "aspect_ratio": "wide", "page_size": 20,
    })
    try:
        hits = get_json(f"{OPENVERSE_IMAGES}?{params}").get("results", [])
    except Exception as exc:
        fail(f"Openverse search failed: {exc}")
    results = []
    for r in hits:
        uid = f"openverse:{r['id']}"
        if uid in known or (r.get("width") or 0) < 800:
            continue
        rank = relevance(query, [t.get("name", "") for t in (r.get("tags") or [])], r.get("title") or "", loose=loose)
        if rank is None:
            continue
        lic = (r.get("license") or "").lower()
        lic_label = "CC0" if lic == "cc0" else "PUBLIC DOMAIN" if lic == "pdm" else f"CC {lic.upper()} {r.get('license_version') or ''}".strip()
        results.append({
            "uid": uid,
            "url": r["url"],
            "ext": "jpg",
            "source": r.get("source"),
            "source_page": r.get("foreign_landing_url"),
            "creator": r.get("creator"),
            "license": lic_label,
            "attribution": r.get("attribution"),
            "credit": f"{(r.get('creator') or 'UNKNOWN').upper()} / {lic_label}",
            "tags": ", ".join(t.get("name", "") for t in (r.get("tags") or [])[:8]),
            "rank": rank,
        })
    return sorted(results, key=lambda r: -r["rank"])


# ---------------------------------------------------------------- normalize

def normalize_video(src: Path, dest: Path, max_seconds: float) -> bool:
    proc = run_cmd([
        "ffmpeg", "-hide_banner", "-y", "-i", str(src), "-t", f"{max_seconds:.2f}", "-an",
        "-vf", "scale=-2:'min(720,ih)'", "-r", "30",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-g", "1", "-keyint_min", "1",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(dest),
    ])
    return proc.returncode == 0 and dest.exists() and dest.stat().st_size > 1000


def normalize_photo(src: Path, dest: Path) -> bool:
    proc = run_cmd([
        "ffmpeg", "-hide_banner", "-y", "-i", str(src), "-frames:v", "1",
        "-vf", "scale='min(1600,iw)':-2", "-q:v", "3", str(dest),
    ])
    return proc.returncode == 0 and dest.exists() and dest.stat().st_size > 1000


def main():
    args = parse_args()
    if not which("ffmpeg"):
        fail("ffmpeg not found on PATH.")
    remotion_dir = find_remotion_dir(args.remotion_dir)
    if not remotion_dir:
        fail("Remotion project not found. Pass --remotion-dir.")

    broll_dir = remotion_dir / "public" / "broll"
    broll_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = broll_dir / "broll-manifest.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {"files": []}
    known = {e["uid"] for e in manifest["files"]}

    log(f"Searching {'Pixabay videos' if args.kind == 'video' else 'Openverse photos'} for '{args.query}'...")
    candidates = (
        search_pixabay_videos(args.query, args.min_duration, known, args.loose)
        if args.kind == "video" else search_openverse_photos(args.query, known, args.loose)
    )
    if not candidates:
        fail(f"No new on-topic, non-AI results for '{args.query}'. Try other keywords or --kind photo.")

    prefix = slugify(args.name or args.query, maxlen=32)
    existing = {Path(e["file"]).name for e in manifest["files"]}
    added = []
    with tempfile.TemporaryDirectory() as tmp:
        for cand in candidates:
            if len(added) >= args.count:
                break
            n = 1
            while f"{prefix}-{n:02d}.{cand['ext']}" in existing:
                n += 1
            dest = broll_dir / f"{prefix}-{n:02d}.{cand['ext']}"
            raw = Path(tmp) / f"raw-{len(added)}"
            if not download(cand["url"], raw):
                continue
            ok = normalize_video(raw, dest, args.max_seconds) if args.kind == "video" else normalize_photo(raw, dest)
            if not ok:
                log(f"  [skip] could not convert {cand['source_page']}")
                continue
            entry = {
                "file": f"broll/{dest.name}",
                "kind": args.kind,
                "query": args.query,
                **{k: cand[k] for k in ("uid", "source", "source_page", "creator", "license", "attribution", "credit", "tags")},
            }
            manifest["files"].append(entry)
            existing.add(dest.name)
            added.append(entry)
            log(f"  + {entry['file']}  <- {cand['source_page']}  [{cand['license']}]")

    write_json(manifest_path, manifest)
    if not added:
        fail("Nothing could be downloaded.")
    print(json.dumps({"status": "ready", "added": [e["file"] for e in added], "manifest": str(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
