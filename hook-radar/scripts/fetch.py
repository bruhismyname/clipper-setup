"""Stage 1 - FETCH.

Pulls, for one YouTube URL:
  - metadata (title, channel, duration, views, chapters)
  - the audience-retention heatmap ("Most Replayed")
  - the caption track (word-level json3 if the video has one)

Two backends, tried in order:
  1. yt-dlp, if installed  (most robust, handles edge cases)
  2. watch-page scrape     (zero dependencies, verified working)

Note on the scrape backend: the bare innertube `/player` endpoint returns
UNPLAYABLE for anonymous requests from many IPs. The watch page itself still
serves the full player response plus `ytInitialData`, and that is where the
heatmap markers live. So we read the page, not the API.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from pathlib import Path

from common import (
    cache_dir,
    fail,
    have_ytdlp,
    log,
    read_json,
    run_cmd,
    video_id_from_url,
    write_json,
    ytdlp_cmd,
)

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": UA,
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ------------------------------------------------------------------ http

def _get_text(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=40) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=40) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


# ------------------------------------------------------------------ js var extraction

def extract_js_object(html: str, var_name: str) -> dict | None:
    """Pull a `var <name> = {...};` blob out of a page.

    Brace counting, string-aware, so nested objects and braces inside strings
    do not break it. This is the standard way to read YouTube's bootstrap vars.
    """
    idx = html.find(var_name + " = ")
    if idx < 0:
        idx = html.find(var_name + "=")
    if idx < 0:
        return None

    start = html.find("{", idx)
    if start < 0:
        return None

    depth = 0
    in_string = False
    escaped = False

    for i in range(start, len(html)):
        ch = html[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                blob = html[start : i + 1]
                try:
                    return json.loads(blob)
                except json.JSONDecodeError as exc:
                    log(f"  could not parse {var_name}: {exc}")
                    return None
    return None


# ------------------------------------------------------------------ heatmap

def parse_heatmap(container: dict) -> list[dict]:
    """Extract Most-Replayed markers from a frameworkUpdates blob.

    Marker shape: {"startMillis": "2140", "durationMillis": "2140",
                   "intensityScoreNormalized": 0.42}
    """
    ranges: list[dict] = []
    mutations = (
        (container.get("frameworkUpdates") or {})
        .get("entityBatchUpdate", {})
        .get("mutations", [])
        or []
    )
    for mut in mutations:
        payload = mut.get("payload") or {}
        entity = payload.get("macroMarkersListEntity")
        if not entity:
            continue
        markers_list = entity.get("markersList") or {}
        if markers_list.get("markerType") != "MARKER_TYPE_HEATMAP":
            continue
        for item in markers_list.get("markers") or []:
            try:
                start_ms = float(item.get("startMillis") or 0)
                dur_ms = float(item.get("durationMillis") or 0)
                value = float(item.get("intensityScoreNormalized") or 0)
            except (TypeError, ValueError):
                continue
            ranges.append(
                {
                    "start_time": round(start_ms / 1000.0, 3),
                    "end_time": round((start_ms + dur_ms) / 1000.0, 3),
                    "value": value,
                }
            )
    ranges.sort(key=lambda r: r["start_time"])
    return ranges


# ------------------------------------------------------------------ meta

def parse_meta_player(player: dict) -> dict:
    vd = player.get("videoDetails") or {}
    mf = (player.get("microformat") or {}).get("playerMicroformatRenderer") or {}
    return {
        "id": vd.get("videoId"),
        "title": vd.get("title"),
        "channel": vd.get("author"),
        "channel_id": vd.get("channelId"),
        "duration": float(vd.get("lengthSeconds") or 0) or None,
        "view_count": int(vd.get("viewCount") or 0) or None,
        "description": (vd.get("shortDescription") or "")[:2000],
        "keywords": (vd.get("keywords") or [])[:30],
        "publish_date": mf.get("publishDate"),
        "category": mf.get("category"),
        "is_live": bool(vd.get("isLiveContent")),
        "chapters": [],
        "source": "watch-page",
    }


def parse_chapters(data: dict) -> list[dict]:
    """Chapters live in the engagement panel of ytInitialData."""
    chapters: list[dict] = []
    try:
        panels = (
            data.get("engagementPanels")
            or data.get("playerOverlays", {})
            .get("playerOverlayRenderer", {})
            .get("decoratedPlayerBarRenderer", {})
            .get("decoratedPlayerBarRenderer", {})
            .get("playerBar", {})
            .get("multiMarkersPlayerBarRenderer", {})
            .get("markersMap", [])
            or []
        )
        for panel in panels:
            if not isinstance(panel, dict):
                continue
            values = (panel.get("value") or {}) if "value" in panel else panel
            for ch in (values.get("chapters") or []):
                cr = ch.get("chapterRenderer") or {}
                title = ((cr.get("title") or {}).get("simpleText")) or ""
                start_ms = cr.get("timeRangeStartMillis") or 0
                chapters.append({"title": title, "start_time": round(float(start_ms) / 1000.0, 2)})
    except (AttributeError, TypeError):
        pass
    return chapters


def parse_caption_tracks(player: dict) -> list[dict]:
    renderer = (
        (player.get("captions") or {}).get("playerCaptionsTracklistRenderer") or {}
    )
    tracks = renderer.get("captionTracks") or []
    out = []
    for t in tracks:
        out.append(
            {
                "url": t.get("baseUrl"),
                "lang": t.get("languageCode"),
                "name": (t.get("name") or {}).get("simpleText", ""),
                "is_asr": t.get("kind") == "asr",
                "vss_id": t.get("vssId", ""),
            }
        )
    return out


# ------------------------------------------------------------------ yt-dlp

def ytdlp_info(url: str) -> dict:
    proc = run_cmd(
        ytdlp_cmd()
        + ["--dump-single-json", "--no-warnings", "--skip-download", "--no-playlist", url]
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return {}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {}


def parse_meta_ytdlp(info: dict) -> dict:
    return {
        "id": info.get("id"),
        "title": info.get("title"),
        "channel": info.get("uploader") or info.get("channel"),
        "channel_id": info.get("channel_id"),
        "duration": float(info.get("duration") or 0) or None,
        "view_count": info.get("view_count"),
        "like_count": info.get("like_count"),
        "comment_count": info.get("comment_count"),
        "upload_date": info.get("upload_date"),
        "description": (info.get("description") or "")[:2000],
        "chapters": [
            {"title": c.get("title", ""), "start_time": float(c.get("start_time") or 0)}
            for c in (info.get("chapters") or [])
        ],
        "source": "yt-dlp",
    }


def parse_heatmap_ytdlp(info: dict) -> list[dict]:
    ranges = []
    for item in info.get("heatmap") or []:
        ranges.append(
            {
                "start_time": float(item.get("start_time") or 0),
                "end_time": float(item.get("end_time") or 0),
                "value": float(item.get("value") or 0),
            }
        )
    ranges.sort(key=lambda r: r["start_time"])
    return ranges


def tracks_from_ytdlp(info: dict) -> list[dict]:
    tracks = []
    for lang in (info.get("subtitles") or {}):
        tracks.append({"url": None, "lang": lang, "name": lang, "is_asr": False})
    for lang in (info.get("automatic_captions") or {}):
        tracks.append({"url": None, "lang": lang, "name": f"auto-{lang}", "is_asr": True})
    return tracks


# ------------------------------------------------------------------ subtitles

def pick_track(tracks: list[dict], language: str = "auto") -> dict | None:
    """Prefer a manual track, prefer the requested language, avoid translation noise."""
    if not tracks:
        return None

    def score(t: dict) -> tuple:
        lang = (t.get("lang") or "").lower()
        if language == "auto":
            lang_penalty = 0 if lang.startswith(("en", "id")) else 1
        else:
            lang_penalty = 0 if lang.startswith(language.lower()) else 1
        # manual beats auto-generated
        return (lang_penalty, 1 if t.get("is_asr") else 0)

    return sorted(tracks, key=score)[0]


def fetch_captions_json3(track: dict) -> dict | None:
    """json3 is the word-level format. Never use SRT here - it loses sub-second gaps."""
    url = track.get("url")
    if not url:
        return None
    if "fmt=" in url:
        url = re.sub(r"fmt=[^&]*", "fmt=json3", url)
    else:
        url += "&fmt=json3"
    try:
        return _get_json(url)
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as exc:
        log(f"  caption fetch failed: {exc}")
        return None


def caption_url_from_info(info: dict, language: str = "auto") -> str | None:
    """Read a json3 caption URL straight out of yt-dlp's metadata.

    yt-dlp already fetched every available track and their URLs when it dumped
    the JSON. Downloading captions therefore needs no second yt-dlp invocation -
    which is what used to trigger the HTTP 429 burst. We just pick a track and
    fetch it over plain HTTP.
    """
    # Preferred languages, in order. "auto" means: the transcript is almost
    # always wanted in the language the video is spoken in, and English is the
    # safe default when that is unknown.
    PREFERRED = ["en", "en-us", "en-gb", "id", "id-id"]

    def rank(lang: str) -> tuple:
        """Lower is better. Exact preferred match first, then preferred prefix,
        then anything - so we never accidentally return Arabic because 'ar' is
        alphabetically shorter than 'en-US'."""
        low = lang.lower()
        if low in PREFERRED:
            return (0, PREFERRED.index(low))
        for i, pref in enumerate(PREFERRED):
            if low.startswith(pref):
                return (1, i)
        return (2, 0)

    def pick(table: dict, lang_filter) -> str | None:
        if not table:
            return None
        langs = list(table.keys())
        if lang_filter:
            matching = [l for l in langs if l.lower().startswith(lang_filter.lower())]
            if matching:
                langs = matching
            # if the requested language is absent, fall through to the
            # preference order rather than silently returning a random one
        for lang in sorted(langs, key=rank):
            for fmt in table.get(lang) or []:
                if fmt.get("ext") == "json3" and fmt.get("url"):
                    return fmt["url"]
        return None

    want = None if language == "auto" else language
    # manual tracks first: better punctuation and no rolling duplicates
    return pick(info.get("subtitles") or {}, want) or pick(
        info.get("automatic_captions") or {}, want
    )


def fetch_captions_ytdlp(url: str, video_id: str, language: str) -> Path | None:
    """Download one caption track as json3, quietly and without a request burst.

    Two things made this noisy before:

    1. `--sub-langs "en.*,en"` is a wildcard. yt-dlp resolves it to every
       English variant YouTube offers (en, en-US, en-GB, en-ar, en-de-DE, ...)
       and fires a request for each. YouTube rate-limits that burst with
       HTTP 429, which is what filled the log with errors even though a caption
       eventually arrived.
    2. Failures were logged at full volume, so an expected miss on the manual
       track looked like a crash before the auto track succeeded.

    So: check the cache first, ask for an explicit short language list, try the
    manual track then the auto track, and stay quiet about misses.
    """
    out_dir = cache_dir() / "subs"
    out_dir.mkdir(parents=True, exist_ok=True)

    # already downloaded for this video? then we are done
    existing = sorted(out_dir.glob(f"{video_id}*.json3"))
    if existing:
        return existing[0]

    if language == "auto":
        # explicit list, ordered by likelihood. No wildcards.
        langs = "en,en-US,en-GB,id,id-ID"
    else:
        langs = language

    # manual captions first (better punctuation), then auto-generated
    attempts = (
        ["--write-subs"],
        ["--write-auto-subs"],
    )
    for flags in attempts:
        run_cmd(
            ytdlp_cmd()
            + [
                "--skip-download",
                *flags,
                "--sub-format", "json3",
                "--sub-langs", langs,
                "-o", str(out_dir / "%(id)s.%(ext)s"),
                "--no-warnings", "--no-playlist", "--quiet",
                url,
            ],
            quiet=True,
        )
        found = sorted(out_dir.glob(f"{video_id}*.json3"))
        if found:
            return found[0]

    return None


# ------------------------------------------------------------------ entry

def fetch(url: str, language: str = "auto", force: bool = False) -> dict:
    video_id = video_id_from_url(url)
    cache = cache_dir() / video_id
    cache.mkdir(parents=True, exist_ok=True)
    meta_path = cache / "meta.json"

    if meta_path.exists() and not force:
        cached = read_json(meta_path)
        if cached.get("meta", {}).get("duration"):
            log(f"  [cache] {video_id}")
            return cached

    log(f"  fetching {video_id} ...")

    meta: dict = {}
    heatmap: list[dict] = []
    tracks: list[dict] = []
    subtitle_path: Path | None = None
    info: dict = {}

    # ---- backend 1: yt-dlp
    if have_ytdlp():
        log("  backend: yt-dlp")
        info = ytdlp_info(url)
        if info:
            meta = parse_meta_ytdlp(info)
            heatmap = parse_heatmap_ytdlp(info)
            tracks = tracks_from_ytdlp(info)

    # ---- backend 2: watch page scrape (also fills gaps from yt-dlp)
    if not meta or not heatmap or not tracks:
        log("  backend: watch-page scrape")
        try:
            html = _get_text(f"https://www.youtube.com/watch?v={video_id}&hl=en")
        except urllib.error.URLError as exc:
            fail(
                f"Could not reach YouTube for {video_id}: {exc}\n"
                "  Check the URL is a public video and the network is up."
            )

        player = extract_js_object(html, "ytInitialPlayerResponse") or {}
        data = extract_js_object(html, "ytInitialData") or {}

        status = (player.get("playabilityStatus") or {}).get("status")
        if status and status not in ("OK", "LIVE_STREAM_OFFLINE"):
            reason = (player.get("playabilityStatus") or {}).get("reason", "unknown")
            fail(
                f"YouTube says this video is not playable: {status} ({reason}).\n"
                "  It may be private, region-locked, age-restricted, or a members-only video."
            )

        if not meta:
            meta = parse_meta_player(player)
        if not heatmap:
            heatmap = parse_heatmap(data) or parse_heatmap(player)
        if not tracks:
            tracks = parse_caption_tracks(player)
        if not meta.get("chapters"):
            meta["chapters"] = parse_chapters(data)

    # ---- captions
    # 1st choice: a URL we already have from the metadata (no extra request)
    direct_url = caption_url_from_info(info, language) if info else None
    if direct_url:
        data_cap = fetch_captions_json3({"url": direct_url})
        if data_cap:
            subtitle_path = cache / "captions.json3"
            write_json(subtitle_path, data_cap)
            log("  captions via metadata URL (no extra request)")

    # 2nd choice: a URL from the watch page
    if subtitle_path is None:
        chosen = pick_track(tracks, language)
        if chosen and chosen.get("url"):
            data_cap = fetch_captions_json3(chosen)
            if data_cap:
                subtitle_path = cache / "captions.json3"
                write_json(subtitle_path, data_cap)
                meta["caption_lang"] = chosen.get("lang")
                meta["caption_is_asr"] = bool(chosen.get("is_asr"))

    # 3rd choice: ask yt-dlp to write the file (rate-limit prone, last resort)
    if subtitle_path is None and have_ytdlp():
        subtitle_path = fetch_captions_ytdlp(url, video_id, language)

    result = {
        "video_id": video_id,
        "url": url,
        "meta": meta,
        "heatmap": heatmap,
        "heatmap_points": len(heatmap),
        "has_heatmap": bool(heatmap),
        "subtitle_path": str(subtitle_path) if subtitle_path else None,
        "caption_tracks": [
            {"lang": t.get("lang"), "is_asr": t.get("is_asr"), "name": t.get("name")}
            for t in tracks
        ],
    }
    write_json(meta_path, result)
    log(
        f"  meta ok | {meta.get('title', '?')[:50]!r} | "
        f"heatmap points: {len(heatmap)} | captions: {'yes' if subtitle_path else 'no'}"
    )
    return result
