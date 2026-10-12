"""web_capture.py - Screenshot a real web page (artist profile, news article, Spotify, Genius ...)
for the browser mockup in Remotion's HtmlMotionLayer.

Uses the installed Chrome/Edge through Playwright (no browser download). Captures a phone-sized
page at 2x so it lands pixel-perfect in the 840px browser card, then the card scrolls through it.

Outputs:
    <remotion>/public/screens/<name>.png
    <remotion>/public/screens/screens-manifest.json   (url, page title, size, capture time)

Usage:
    python hook-radar/scripts/web_capture.py "https://open.spotify.com/artist/..." --name skillibeng-spotify
    python hook-radar/scripts/web_capture.py "<NEWS_URL>" --name headline --selector "article h1" --device desktop

Then place it in a clip:
    export_remotion.py <VIDEO_ID> --candidate c01 --html-type browser --html-screenshot screens/skillibeng-spotify.png --html-at 8
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import fail, log, read_json, slugify, write_json  # noqa: E402
from export_remotion import find_remotion_dir  # noqa: E402

# 420 CSS px at 2x = 840 px, the exact width of the browser card in HtmlMotionLayer
DEVICES = {
    "mobile": {
        "viewport": {"width": 420, "height": 900},
        "device_scale_factor": 2,
        "is_mobile": True,
        "has_touch": True,
        "user_agent": (
            "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36"
        ),
    },
    "desktop": {"viewport": {"width": 1280, "height": 800}, "device_scale_factor": 1},
}

# Cookie / consent buttons worth one click before the screenshot
CONSENT = re.compile(r"^(accept( all)?( cookies)?|i agree|agree|allow all|got it|ok|setuju|terima( semua)?)$", re.IGNORECASE)


def parse_args():
    ap = argparse.ArgumentParser(prog="web_capture", description="Screenshot a web page for the Remotion browser mockup.")
    ap.add_argument("url", help="Page to capture")
    ap.add_argument("--name", default="", help="Output name (default: slug of the page host + path)")
    ap.add_argument("--device", choices=list(DEVICES), default="mobile", help="mobile (default) or desktop layout")
    ap.add_argument("--selector", default="", help="Capture only this element (CSS selector), e.g. 'article h1'")
    ap.add_argument("--screens", type=float, default=2.5, help="Page height to capture, in viewport heights (default: 2.5)")
    ap.add_argument("--wait", type=int, default=2500, help="Extra wait after load in ms (default: 2500)")
    ap.add_argument("--remotion-dir", default=None, help="Remotion project dir (auto-detected if omitted)")
    return ap.parse_args()


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def launch(p):
    for channel in ("chrome", "msedge"):
        try:
            return p.chromium.launch(channel=channel, headless=True)
        except Exception:
            continue
    return p.chromium.launch(headless=True)


def dismiss_popups(page) -> None:
    for frame in page.frames:
        try:
            buttons = frame.get_by_role("button", name=CONSENT)
            if buttons.count():
                buttons.first.click(timeout=1500)
                page.wait_for_timeout(600)
                return
        except Exception:
            continue
    page.keyboard.press("Escape")


def main():
    args = parse_args()
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        fail("Playwright missing. Run: .venv/Scripts/python.exe -m pip install playwright")
    remotion_dir = find_remotion_dir(args.remotion_dir)
    if not remotion_dir:
        fail("Remotion project not found. Pass --remotion-dir.")

    screens_dir = remotion_dir / "public" / "screens"
    screens_dir.mkdir(parents=True, exist_ok=True)
    name = slugify(args.name or re.sub(r"^https?://(www\.)?", "", args.url), maxlen=40)
    dest = screens_dir / f"{name}.png"
    device = DEVICES[args.device]

    with sync_playwright() as p:
        browser = launch(p)
        context = browser.new_context(**device, locale="en-US", color_scheme="dark")
        page = context.new_page()
        log(f"Opening {args.url} ({args.device})...")
        try:
            page.goto(args.url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            log("  page kept loading; capturing what is there")
        page.wait_for_timeout(args.wait)
        dismiss_popups(page)
        title = page.title()

        if args.selector:
            el = page.locator(args.selector).first
            if not el.count():
                browser.close()
                fail(f"Selector '{args.selector}' not found on the page.")
            el.scroll_into_view_if_needed()
            el.screenshot(path=str(dest))
        else:
            vp = device["viewport"]
            page_height = page.evaluate("() => document.documentElement.scrollHeight")
            clip_height = min(page_height, int(vp["height"] * args.screens))
            page.screenshot(path=str(dest), full_page=True,
                            clip={"x": 0, "y": 0, "width": vp["width"], "height": clip_height})
        browser.close()

    width, height = png_size(dest)
    manifest_path = screens_dir / "screens-manifest.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {"files": []}
    entry = {
        "file": f"screens/{dest.name}",
        "url": args.url,
        "title": title,
        "device": args.device,
        "width": width,
        "height": height,
        "captured_at": datetime.now().isoformat(timespec="seconds"),
    }
    manifest["files"] = [e for e in manifest["files"] if e["file"] != entry["file"]] + [entry]
    write_json(manifest_path, manifest)
    log(f"  + {entry['file']} ({width}x{height}) \"{title}\"")
    print(json.dumps({"status": "ready", **entry}, indent=2))


if __name__ == "__main__":
    main()
