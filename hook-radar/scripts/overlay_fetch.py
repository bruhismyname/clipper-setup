"""overlay_fetch.py - Fetch keyword overlay images for Style B "Fullbleed Speaker".

Style B pops a picture of whatever the speaker names into the lower half of the frame
(a "visual dictionary", ATM of @dailyyskchaos). Sources are never AI-made:
    --emoji     -> Noto Color Emoji 2D PNG 512px (Apache 2.0 / OFL 1.1, no attribution needed)
    photo query -> Openverse photos (CC0 / CC BY / CC BY-SA, NC/ND excluded) or
                   Pixabay photos (--source pixabay, PIXABAY_API_KEY in .env, no attribution)
Search results reuse broll_fetch.py's relevance ranking and AI-tag filter. No background
removal or any other AI processing is applied: photos keep their rectangle (rounded in Remotion).

Outputs:
    <remotion>/public/overlays/<name>-NN.jpg
    <remotion>/public/overlays/emoji/emoji_uXXXX.png
    <remotion>/public/overlays/overlays-manifest.json   (source page, creator, license, credit per file)

Usage:
    python hook-radar/scripts/overlay_fetch.py --emoji 🤔 😳 💀
    python hook-radar/scripts/overlay_fetch.py "green beans" --count 2
    python hook-radar/scripts/overlay_fetch.py "cruise ship" --source pixabay --count 2

Then place them in a Style B clip:
    export_remotion.py <VIDEO_ID> --style fullbleed ... --overlay emoji:🤔@0.4+1.2 --overlay overlays/green-beans-01.jpg@6.2+1.5
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import emoji_filename, env_key, fail, log, read_json, run_cmd, slugify, which, write_json  # noqa: E402
from export_remotion import find_remotion_dir  # noqa: E402
from broll_fetch import download, get_json, relevance, search_openverse_photos  # noqa: E402

NOTO_PNG = "https://raw.githubusercontent.com/googlefonts/noto-emoji/main/2D/png/512/{name}"
PIXABAY_IMAGES = "https://pixabay.com/api/"
NO_CREDIT_LICENSES = ("CC0", "PUBLIC DOMAIN", "Pixabay Content License", "Apache-2.0/OFL-1.1 (Noto Emoji)")


def parse_args():
    ap = argparse.ArgumentParser(prog="overlay_fetch", description="Fetch non-AI keyword overlay images for Style B.")
    ap.add_argument("query", nargs="?", default="", help="Photo search keywords, e.g. 'green beans'")
    ap.add_argument("--emoji", nargs="+", default=[], help="Emoji to fetch as Noto PNGs, e.g. --emoji 🤔 😳")
    ap.add_argument("--source", choices=["openverse", "pixabay"], default="openverse", help="Photo source (default: openverse)")
    ap.add_argument("--count", type=int, default=2, help="How many photos to download (default: 2)")
    ap.add_argument("--name", default="", help="File name prefix (default: slug of the query)")
    ap.add_argument("--max-width", type=int, default=900, help="Resize photos to at most this width (default: 900)")
    ap.add_argument("--loose", action="store_true", help="Accept results whose tags only contain the words separately")
    ap.add_argument("--remotion-dir", default=None, help="Remotion project dir (auto-detected if omitted)")
    args = ap.parse_args()
    if not args.query and not args.emoji:
        ap.error("give a photo query and/or --emoji")
    return args


def search_pixabay_photos(query: str, known: set[str], loose: bool) -> list[dict]:
    key = env_key("PIXABAY_API_KEY")
    if not key:
        fail("PIXABAY_API_KEY not found. Add it to D:/Project/clonee/.env")
    params = urllib.parse.urlencode({"key": key, "q": query, "image_type": "photo", "per_page": 50,
                                     "safesearch": "true", "order": "popular", "min_width": 900})
    try:
        hits = get_json(f"{PIXABAY_IMAGES}?{params}").get("hits", [])
    except Exception as exc:
        fail(f"Pixabay search failed: {exc}")
    results = []
    for h in hits:
        uid = f"pixabay-img:{h['id']}"
        if uid in known:
            continue
        rank = relevance(query, (h.get("tags") or "").split(","), loose=loose)
        if rank is None:
            continue
        results.append({
            "uid": uid, "url": h.get("largeImageURL") or h.get("webformatURL"), "source": "pixabay",
            "source_page": h.get("pageURL"), "creator": h.get("user"), "license": "Pixabay Content License",
            "attribution": None, "credit": "", "tags": h.get("tags"), "rank": rank,
        })
    return sorted(results, key=lambda r: -r["rank"])


def normalize_photo(src: Path, dest: Path, max_width: int) -> bool:
    proc = run_cmd(["ffmpeg", "-hide_banner", "-y", "-i", str(src), "-frames:v", "1",
                    "-vf", f"scale='min({max_width},iw)':-2", "-q:v", "3", str(dest)])
    return proc.returncode == 0 and dest.exists() and dest.stat().st_size > 1000


def fetch_emoji(emojis: list[str], overlay_dir: Path, manifest: dict) -> list[dict]:
    emoji_dir = overlay_dir / "emoji"
    emoji_dir.mkdir(parents=True, exist_ok=True)
    have = {e["file"] for e in manifest["files"]}
    added = []
    for em in emojis:
        name = emoji_filename(em)
        rel = f"overlays/emoji/{name}"
        if rel in have and (emoji_dir / name).exists():
            log(f"  = {rel} (already there)")
            continue
        if not download(NOTO_PNG.format(name=name), emoji_dir / name):
            log(f"  [skip] Noto has no PNG for {em} ({name}); pick another emoji")
            continue
        entry = {"file": rel, "kind": "emoji", "query": em, "uid": f"noto:{name}", "source": "noto-emoji",
                 "source_page": "https://github.com/googlefonts/noto-emoji", "creator": "Google",
                 "license": "Apache-2.0/OFL-1.1 (Noto Emoji)", "attribution": None, "credit": "", "tags": em}
        manifest["files"].append(entry)
        added.append(entry)
        log(f"  + {rel}")
    return added


def fetch_photos(args, overlay_dir: Path, manifest: dict) -> list[dict]:
    known = {e["uid"] for e in manifest["files"]}
    log(f"Searching {args.source} photos for '{args.query}'...")
    candidates = (search_pixabay_photos(args.query, known, args.loose) if args.source == "pixabay"
                  else search_openverse_photos(args.query, known, args.loose))
    if not candidates:
        fail(f"No new on-topic, non-AI photos for '{args.query}'. Try other keywords, --source pixabay or --loose.")
    prefix = slugify(args.name or args.query, maxlen=32)
    existing = {Path(e["file"]).name for e in manifest["files"]}
    added = []
    with tempfile.TemporaryDirectory() as tmp:
        for cand in candidates:
            if len(added) >= args.count:
                break
            n = 1
            while f"{prefix}-{n:02d}.jpg" in existing:
                n += 1
            dest = overlay_dir / f"{prefix}-{n:02d}.jpg"
            raw = Path(tmp) / f"raw-{len(added)}"
            if not download(cand["url"], raw) or not normalize_photo(raw, dest, args.max_width):
                log(f"  [skip] {cand['source_page']}")
                continue
            # CC0 / Pixabay need no credit; CC BY / BY-SA credit is shown under the overlay
            credit = "" if cand["license"] in NO_CREDIT_LICENSES else cand["credit"]
            entry = {"file": f"overlays/{dest.name}", "kind": "photo", "query": args.query,
                     **{k: cand[k] for k in ("uid", "source", "source_page", "creator", "license", "attribution", "tags")},
                     "credit": credit}
            manifest["files"].append(entry)
            existing.add(dest.name)
            added.append(entry)
            log(f"  + {entry['file']}  <- {cand['source_page']}  [{cand['license']}]")
    return added


def main():
    args = parse_args()
    if not which("ffmpeg"):
        fail("ffmpeg not found on PATH.")
    remotion_dir = find_remotion_dir(args.remotion_dir)
    if not remotion_dir:
        fail("Remotion project not found. Pass --remotion-dir.")
    overlay_dir = remotion_dir / "public" / "overlays"
    overlay_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = overlay_dir / "overlays-manifest.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {"files": []}

    added = fetch_emoji(args.emoji, overlay_dir, manifest) if args.emoji else []
    if args.query:
        added += fetch_photos(args, overlay_dir, manifest)
    write_json(manifest_path, manifest)
    if not added and not args.emoji:
        fail("Nothing could be downloaded.")
    print(json.dumps({"status": "ready", "added": [e["file"] for e in added], "manifest": str(manifest_path)},
                     indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
