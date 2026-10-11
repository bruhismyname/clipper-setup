"""Shared helpers for hook-radar. Stdlib only (except optional yt-dlp/faster-whisper)."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------- paths

def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


def workspace() -> Path:
    """Where all run artifacts live. Override with HOOK_RADAR_WORKSPACE."""
    env = os.environ.get("HOOK_RADAR_WORKSPACE")
    if env:
        p = Path(env).expanduser()
    else:
        p = skill_root() / "workspace"
    p.mkdir(parents=True, exist_ok=True)
    return p


def run_dir(video_id: str) -> Path:
    p = workspace() / "runs" / video_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def cache_dir() -> Path:
    p = workspace() / "cache"
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------- logging

def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def fail(msg: str, code: int = 1):
    """Fail loud, never guess. (Pattern borrowed from Clip-Engine.)"""
    print(f"\nERROR: {msg}", file=sys.stderr, flush=True)
    sys.exit(code)


# ---------------------------------------------------------------- tools

def which(name: str) -> str | None:
    return shutil.which(name)


def have_ytdlp() -> bool:
    if which("yt-dlp"):
        return True
    try:
        import yt_dlp  # noqa: F401
        return True
    except Exception:
        return False


def run_cmd(args: list[str], cwd: Path | None = None, quiet: bool = False) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0 and not quiet:
        log(f"  [cmd failed rc={proc.returncode}] {' '.join(args[:4])}...")
        if proc.stderr:
            log("  " + proc.stderr.strip().splitlines()[-1][:300])
    return proc


def ytdlp_cmd() -> list[str]:
    """Prefer the yt-dlp executable; fall back to python -m yt_dlp."""
    if which("yt-dlp"):
        return ["yt-dlp"]
    return [sys.executable, "-m", "yt_dlp"]


# ---------------------------------------------------------------- text

def parse_time(text: str) -> float:
    """'1:02:03' | '02:03' | '93.5' -> seconds."""
    text = text.strip()
    if ":" not in text:
        return float(text)
    parts = [float(p) for p in text.split(":")]
    total = 0.0
    for p in parts:
        total = total * 60 + p
    return total


def fmt_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    if h:
        return f"{h}:{m:02d}:{s:05.2f}"
    return f"{m}:{s:05.2f}"


def slugify(text: str, maxlen: int = 48) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text[:maxlen] or "clip"


def video_id_from_url(url: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|/shorts/|/embed/|/live/)([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url.strip()):
        return url.strip()
    fail(f"Could not read a YouTube video id from: {url}")


# ---------------------------------------------------------------- io

def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- options

DEFAULT_OPTIONS = {
    "platform": "tiktok",
    "min_duration": 15,
    "max_duration": 45,
    "ideal_duration": 28,
    "top_n": 10,
    "transcript": "auto",          # auto | captions | whisper
    "whisper_model": "small",
    "whisper_device": "auto",
    "language": "auto",
    "use_heatmap": True,
    "download_video": False,
    "max_height": 1080,
    "allow_non_youtube": False,
}
