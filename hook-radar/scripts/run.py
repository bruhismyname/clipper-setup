"""hook-radar - one command, one YouTube URL, ranked TikTok hook candidates.

    python scripts/run.py "https://www.youtube.com/watch?v=XXXX"

Pipeline: fetch -> heatmap -> transcript -> score -> report

Outputs land in <workspace>/runs/<video_id>/ :
    meta.json          raw fetch result (metadata, heatmap, caption info)
    words.json         word-level transcript
    phrases.json       phrase-level transcript
    transcript_packed.md   the agent's reading view
    candidates.json    ranked clips with scores + evidence
    report.md          human/agent readable summary

The script does the mechanical work. The agent does the taste work - it must
read candidates.json, re-rank with the rubric in references/, and write the
final hooks. See SKILL.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import (  # noqa: E402
    DEFAULT_OPTIONS,
    fail,
    fmt_time,
    log,
    read_json,
    run_cmd,
    video_id_from_url,
    write_json,
    run_dir,
)

import fetch as fetch_mod  # noqa: E402
import heatmap as heatmap_mod  # noqa: E402
import score as score_mod  # noqa: E402
import transcript as transcript_mod  # noqa: E402


def parse_args(argv=None):
    ap = argparse.ArgumentParser(
        prog="hook-radar",
        description="Find TikTok hook moments in a YouTube video, ranked.",
    )
    ap.add_argument("url", help="YouTube URL or 11-char video id")
    ap.add_argument("--platform", default="tiktok", choices=["tiktok", "shorts", "reels"])
    ap.add_argument("--top", type=int, default=10, help="how many candidates to keep (default 10)")
    ap.add_argument("--min", type=float, default=15.0, help="min clip seconds (default 15)")
    ap.add_argument("--max", type=float, default=45.0, help="max clip seconds (default 45)")
    ap.add_argument("--ideal", type=float, default=28.0, help="ideal clip seconds (default 28)")
    ap.add_argument(
        "--transcript",
        default="auto",
        choices=["auto", "captions", "whisper"],
        help="auto = captions if available else whisper",
    )
    ap.add_argument("--whisper-model", default="small", help="tiny|base|small|medium|large-v3")
    ap.add_argument("--whisper-device", default="auto", help="auto|cpu|cuda")
    ap.add_argument("--language", default="auto", help="caption/whisper language code")
    ap.add_argument("--download-video", action="store_true", help="also fetch the MP4 (needed for whisper/rendering)")
    ap.add_argument("--max-height", type=int, default=1080)
    ap.add_argument("--force", action="store_true", help="ignore cache, refetch everything")
    ap.add_argument("--from-meta", help="rescore from an existing meta.json without refetching")
    ap.add_argument("--json", action="store_true", help="print only the JSON payload")
    ap.add_argument("--workspace", help="override workspace dir")
    return ap.parse_args(argv)


def download_video(url: str, rd: Path, max_height: int) -> Path | None:
    target = rd / "source.mp4"
    if target.exists():
        log("  [cache] source video")
        return target
    if not fetch_mod.have_ytdlp():
        fail("--download-video needs yt-dlp:  pip install -U yt-dlp")
    log("  downloading video ...")
    proc = run_cmd(
        fetch_mod.ytdlp_cmd()
        + [
            # H.264 + AAC first (same as yt-dlp-edit.conf): YouTube's default AV1/Opus pick fails to merge
            # here and is unsupported by Premiere; fall back to any codec only if H.264 is missing
            "-f", f"bv*[vcodec^=avc1][height<={max_height}]+ba[acodec^=mp4a]/bv*[height<={max_height}]+ba/b",
            "--merge-output-format", "mp4",
            "--no-playlist",
            "--no-warnings",
            "-o", str(target),
            url,
        ]
    )
    if proc.returncode != 0 or not target.exists():
        log("  download failed - continuing without the video file")
        return None
    return target


def build_report(result: dict, options: dict) -> str:
    meta = result["meta"]
    cands = result["candidates"]
    lines: list[str] = []

    lines.append(f"# Hook Radar - {meta.get('title', 'unknown')}")
    lines.append("")
    dur = meta.get("duration") or 0
    lines.append(
        f"- **Source**: {meta.get('channel', '?')} | {fmt_time(dur)} | "
        f"{meta.get('view_count') or '?'} views"
    )
    lines.append(f"- **URL**: {result.get('url')}")
    lines.append(
        f"- **Transcript**: {result['transcript']['source']} "
        f"({result['transcript']['words']} words, {result['transcript']['phrases']} phrases)"
    )
    ct = result.get("content_type") or {}
    if ct.get("type") in ("music", "mixed", "sparse"):
        icon = "MUSIC" if ct["type"] == "music" else ct["type"].upper()
        lines.append(f"- **Content type**: **{icon}** - {ct.get('reason', '')}")
    else:
        lines.append(f"- **Content type**: speech - {ct.get('reason', '')}")

    hm = result["heatmap"]
    if not hm["available"]:
        hm_label = "NOT published for this video"
    elif hm["peaks"]:
        hm_label = f"{len(hm['peaks'])} peaks found"
    else:
        hm_label = "curve present, but no standout peak"
    lines.append(f"- **Retention heatmap**: {hm_label}")
    lines.append(f"- **Platform**: {options['platform']} | target {options['min_duration']:.0f}-{options['max_duration']:.0f}s")
    lines.append("")

    if not hm["available"]:
        lines.append(
            "> No Most-Replayed data for this video. Scores lean on transcript signals only - "
            "treat the ranking as a shortlist, not a verdict."
        )
        lines.append("")
    elif not hm["peaks"]:
        lines.append(
            "> The retention curve exists but shows no distinct peak: attention is flat, or it "
            "simply decays from the intro (common on music videos). Scores lean on transcript "
            "signals. Treat the ranking as a shortlist, not a verdict."
        )
        lines.append("")

    ct_type = (result.get("content_type") or {}).get("type")
    if ct_type in ("music", "sparse"):
        lines.append(
            "> **This source is a poor fit for hook finding.** " + (result.get("content_type") or {}).get("reason", "") + "\n"
            "> Hook selection needs speech: a line that opens a curiosity gap and a payoff that lands.\n"
            "> Report this to the user instead of presenting a thin shortlist as a result."
        )
        lines.append("")

    if not cands:
        lines.append("## Ranked candidates")
        lines.append("")
        lines.append(
            "No candidates cleared the bar. That is a finding, not a failure - say so plainly. "
            "Check `transcript_packed.md` and `content_type` above before concluding anything."
        )
        lines.append("")
        lines.append("## Agent handoff")
        lines.append("")
        lines.append(
            "Report why nothing qualified, and what would need to change (a speech-based source, "
            "a different video). Do not invent moments to fill the list."
        )
        lines.append("")
        return "\n".join(lines)

    lines.append("## Ranked candidates")
    lines.append("")
    for c in cands:
        s = c["scores"]
        lines.append(
            f"### {c['id']} - composite {s['composite']}  "
            f"(hook {s['hook']} / retention {s['retention']} / fit {s['fit']})"
        )
        lines.append(f"- **Window**: `{c['start_hms']}` -> `{c['end_hms']}` ({c['duration']}s)")
        lines.append(f"- **Origin**: {c['origin']}")
        lines.append(f"- **Opens with**: \"{c['first_line']}\"")
        lines.append(f"- **Ends on**: \"{c['last_line']}\"")
        sig = c["evidence"].get("signals") or {}
        if sig:
            flat = "; ".join(f"{k}: {', '.join(v[:3])}" for k, v in sig.items())
            lines.append(f"- **Hook signals**: {flat}")
        lines.append(f"- **Why**: {' | '.join(c['evidence']['hook'][:3])}")
        if c["evidence"].get("retention_stats"):
            st = c["evidence"]["retention_stats"]
            lines.append(
                f"- **Retention**: mean {st['mean']:.2f}, peak {st['max']:.2f}, "
                f"delta {st['delta_vs_baseline']:+.3f} vs baseline"
            )
        lines.append("")

    lines.append("## Agent handoff")
    lines.append("")
    lines.append(
        "Scores above are mechanical. Before returning results, follow `references/scoring-rubric.md`:\n"
        "re-rank the top candidates on judgement, reject context traps, and write the final TikTok hook\n"
        "(0-3s), on-screen text, caption, and hashtags for each. Flag any clip whose meaning changes when\n"
        "it is lifted out of the full video."
    )
    lines.append("")
    return "\n".join(lines)


def main(argv=None) -> int:
    args = parse_args(argv)

    options = dict(DEFAULT_OPTIONS)
    options.update(
        {
            "platform": args.platform,
            "min_duration": args.min,
            "max_duration": args.max,
            "ideal_duration": args.ideal,
            "top_n": args.top,
            "transcript": args.transcript,
            "whisper_model": args.whisper_model,
            "whisper_device": args.whisper_device,
            "language": args.language,
            "max_height": args.max_height,
        }
    )

    if args.workspace:
        import os

        os.environ["HOOK_RADAR_WORKSPACE"] = args.workspace

    # ---------------------------------------------------------- fetch
    if args.from_meta:
        fetched = read_json(Path(args.from_meta))
        video_id = fetched.get("video_id") or video_id_from_url(args.url)
        log(f"[1/5] fetch: reusing {args.from_meta}")
    else:
        log("[1/5] fetch")
        fetched = fetch_mod.fetch(args.url, language=args.language, force=args.force)
        video_id = fetched["video_id"]

    rd = run_dir(video_id)
    meta = fetched.get("meta") or {}
    if not meta.get("duration"):
        fail("Could not read video metadata. Check the URL is public and reachable.")

    # ---------------------------------------------------------- video (optional)
    video_path = None
    if args.download_video:
        video_path = download_video(fetched["url"], rd, args.max_height)

    # ---------------------------------------------------------- heatmap
    log("[2/5] heatmap")
    hm = heatmap_mod.analyze(fetched.get("heatmap") or [], top_n=15)
    write_json(rd / "heatmap.json", hm)

    # ---------------------------------------------------------- transcript
    log("[3/5] transcript")
    if args.force:
        # --force must also redo the transcript (e.g. switching captions -> whisper)
        for name in ("words.json", "phrases.json", "sentences.json", "transcript_packed.md"):
            (rd / name).unlink(missing_ok=True)
    tr = transcript_mod.build(
        fetched,
        rd,
        mode=args.transcript,
        whisper_model=args.whisper_model,
        whisper_device=args.whisper_device,
        language=args.language,
        video_path=video_path,
    )

    # ---------------------------------------------------------- content check
    ctype = score_mod.detect_content_type(tr["phrases"], tr["words"])

    # ---------------------------------------------------------- score
    log("[4/5] score")
    candidates = score_mod.build_candidates(
        tr["words"], tr["phrases"], fetched.get("heatmap") or [], meta, options,
        sentences=tr.get("sentences") or [],
    )
    candidates = candidates[: args.top]

    result = {
        "schema": "hook-radar/v1",
        "video_id": video_id,
        "url": fetched.get("url"),
        "meta": meta,
        "options": options,
        "heatmap": hm,
        "content_type": ctype,
        "transcript": {
            "source": tr["source"],
            "words": len(tr["words"]),
            "phrases": len(tr["phrases"]),
            "sentences": len(tr.get("sentences") or []),
            "packed_path": tr["packed_path"],
        },
        "candidates": candidates,
        "artifacts": {
            "run_dir": str(rd),
            "candidates": str(rd / "candidates.json"),
            "report": str(rd / "report.md"),
            "packed_transcript": tr["packed_path"],
        },
    }
    write_json(rd / "candidates.json", result)
    report = build_report(result, options)
    (rd / "report.md").write_text(report, encoding="utf-8")

    # ---------------------------------------------------------- out
    log("[5/5] done")
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(report)
        print("---")
        print(f"run dir: {rd}")
        print(f"machine-readable: {rd / 'candidates.json'}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        raise SystemExit(130)
