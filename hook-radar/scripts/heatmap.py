"""Stage 2 - HEATMAP.

Turns YouTube's "Most Replayed" curve into ranked retention peaks.

This is the part that most clipper tools guess at. YouTube already measured
which seconds real viewers scrub back to; that is the single best free signal
for "what will hold attention". We do not invent it, we read it.

The curve is 100 points at ~1.2% intensity resolution (values 0..1), so a
"peak" here means a local maximum sustained above the video's own baseline -
not a one-sample blip.
"""
from __future__ import annotations

from common import log

# Peak detection tuning. Values are fractions of the curve's own range, so the
# logic behaves the same on a 4-minute video and a 4-hour stream.
MIN_PROMINENCE = 0.18      # peak must rise this far above the local valley
MIN_REL_LEVEL = 0.45       # and sit this far up the video's own 0..max range
SMOOTH_WINDOW = 3          # moving average, removes single-sample spikes


def _smooth(values: list[float], window: int = SMOOTH_WINDOW) -> list[float]:
    if window <= 1 or len(values) < window:
        return list(values)
    half = window // 2
    out = []
    for i in range(len(values)):
        lo = max(0, i - half)
        hi = min(len(values), i + half + 1)
        chunk = values[lo:hi]
        out.append(sum(chunk) / len(chunk))
    return out


def _interpolate_at(heatmap: list[dict], t: float) -> float:
    """Sample the retention curve at time t (seconds).

    Each heatmap entry IS the measurement for its own bucket, so the correct
    read is a bucket lookup. The earlier implementation interpolated between
    bucket *starts* while testing against bucket *ends*, so any t inside the
    second bucket produced frac > 1 - extrapolation - and reported intensities
    above the curve's own maximum (0.5 -> 1.2 on a 0..1 scale).
    """
    if not heatmap:
        return 0.0
    if t <= heatmap[0]["start_time"]:
        return float(heatmap[0]["value"])
    for point in heatmap:
        if point["start_time"] <= t < point["end_time"]:
            return float(point["value"])
    return float(heatmap[-1]["value"])


def detect_peaks(heatmap: list[dict], min_gap: float = 8.0) -> list[dict]:
    """Return local maxima of the retention curve, strongest first."""
    if not heatmap:
        return []

    times = [r["start_time"] for r in heatmap]
    raw = [float(r.get("value") or 0.0) for r in heatmap]
    vals = _smooth(raw)

    lo, hi = min(vals), max(vals)
    span = max(1e-6, hi - lo)
    peaks: list[dict] = []

    for i in range(1, len(vals) - 1):
        if not (vals[i] >= vals[i - 1] and vals[i] >= vals[i + 1]):
            continue

        # walk left/right to the nearest valleys for prominence
        left = vals[i]
        j = i - 1
        while j >= 0 and vals[j] <= vals[i]:
            left = min(left, vals[j])
            j -= 1
        right = vals[i]
        k = i + 1
        while k < len(vals) and vals[k] <= vals[i]:
            right = min(right, vals[k])
            k += 1
        prominence = vals[i] - max(left, right)

        rel_level = (vals[i] - lo) / span
        if prominence < MIN_PROMINENCE or rel_level < MIN_REL_LEVEL:
            continue

        peaks.append(
            {
                "time": times[i],
                "level": round(vals[i], 4),
                "raw_level": round(raw[i], 4),
                "prominence": round(prominence, 4),
                "rel_level": round(rel_level, 4),
                "rank_in_video": 0,  # filled below
            }
        )

    # enforce minimum spacing, keep the stronger of two neighbours
    peaks.sort(key=lambda p: p["time"])
    spaced: list[dict] = []
    for p in peaks:
        if spaced and p["time"] - spaced[-1]["time"] < min_gap:
            if p["level"] > spaced[-1]["level"]:
                spaced[-1] = p
            continue
        spaced.append(p)

    spaced.sort(key=lambda p: p["level"], reverse=True)
    for idx, p in enumerate(spaced, 1):
        p["rank_in_video"] = idx
    return spaced


def baseline_stats(heatmap: list[dict]) -> dict:
    if not heatmap:
        return {"mean": 0.0, "max": 0.0, "min": 0.0, "points": 0}
    vals = [float(r.get("value") or 0.0) for r in heatmap]
    return {
        "mean": round(sum(vals) / len(vals), 4),
        "max": round(max(vals), 4),
        "min": round(min(vals), 4),
        "points": len(vals),
    }


def segment_retention(heatmap: list[dict], start: float, end: float) -> dict:
    """Retention stats for a candidate window - used when scoring clips."""
    if not heatmap or end <= start:
        return {"mean": 0.0, "max": 0.0, "min": 0.0, "samples": 0, "delta_vs_baseline": 0.0}

    samples = []
    step = max(0.5, (end - start) / 40.0)
    t = start
    while t <= end:
        samples.append(_interpolate_at(heatmap, t))
        t += step
    # hard clamp: the curve is normalised 0..1, so anything outside is a bug
    samples = [min(1.0, max(0.0, s)) for s in samples]
    if not samples:
        return {"mean": 0.0, "max": 0.0, "min": 0.0, "samples": 0, "delta_vs_baseline": 0.0}

    base = baseline_stats(heatmap)["mean"]
    mean = sum(samples) / len(samples)
    return {
        "mean": round(mean, 4),
        "max": round(max(samples), 4),
        "min": round(min(samples), 4),
        "samples": len(samples),
        "delta_vs_baseline": round(mean - base, 4),
    }


def analyze(heatmap: list[dict], top_n: int = 12) -> dict:
    """Detect peaks and report honestly what the curve actually says.

    Three distinct states, and they must not be confused with each other:
      - no curve at all      -> Most Replayed was never published
      - curve, but no peaks  -> published, yet nothing stands out (e.g. a music
                                video whose intensity just decays from the intro)
      - curve with peaks     -> usable audience data
    """
    peaks = detect_peaks(heatmap)[:top_n]
    stats = baseline_stats(heatmap)
    available = bool(heatmap)

    if peaks:
        log(f"  retention peaks found: {len(peaks)} (baseline mean {stats['mean']}, max {stats['max']})")
    elif available:
        log(
            f"  retention curve present ({stats['points']} points, max {stats['max']}) "
            "but no distinct peak - attention is flat or decays from the intro"
        )
    else:
        log("  no retention data: this video has no published Most Replayed curve")

    return {
        "peaks": peaks,
        "baseline": stats,
        "available": available,
        "note": (
            None
            if peaks
            else (
                "curve present but no standout moment"
                if available
                else "no Most Replayed data published for this video"
            )
        ),
    }
